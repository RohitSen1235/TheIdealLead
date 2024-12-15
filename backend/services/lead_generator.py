import asyncio
from typing import List, Tuple, Dict, Optional, Set
import aiohttp
from bs4 import BeautifulSoup
import os
import csv
from datetime import datetime, timedelta
import groq
from urllib.parse import quote_plus, unquote
import json
from config import settings
import logging
import random
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchResult:
    def __init__(self, profiles: List[dict], total_found: int, warnings: List[str] = None):
        self.profiles = profiles
        self.total_found = total_found
        self.warnings = warnings or []

class ProxyManager:
    def __init__(self, proxies: List[Dict[str, str]]):
        self.proxies = proxies
        self.current_index = 0
        self.error_counts = defaultdict(int)
        self.cooldown_until = defaultdict(lambda: datetime.min)
        self.success_counts = defaultdict(int)
        self.last_used = defaultdict(lambda: datetime.min)
        
        # Configuration
        self.max_errors = 2  # Max errors before cooldown
        self.cooldown_minutes = 5  # Cooldown period in minutes
        self.min_delay = 1  # Minimum seconds between requests per proxy
        
        logger.info(f"Initialized ProxyManager with {len(proxies)} proxies")

    def _get_proxy_key(self, proxy: Dict[str, str]) -> str:
        """Generate a unique key for a proxy"""
        return proxy['url']

    async def get_next_proxy(self) -> Tuple[Optional[Dict[str, str]], Optional[aiohttp.BasicAuth]]:
        """Get the next available proxy with the least errors/cooldown"""
        if not self.proxies:
            return None, None

        now = datetime.now()
        available_proxies = []

        # Find available proxies (not in cooldown and not recently used)
        for proxy in self.proxies:
            proxy_key = self._get_proxy_key(proxy)
            if (now >= self.cooldown_until[proxy_key] and 
                (now - self.last_used[proxy_key]).total_seconds() >= self.min_delay):
                available_proxies.append(proxy)

        if not available_proxies:
            # If no proxies are available, wait for the one with shortest cooldown
            min_wait = min((self.cooldown_until[self._get_proxy_key(p)] - now).total_seconds() 
                         for p in self.proxies)
            if min_wait > 0:
                await asyncio.sleep(min_wait)
            return await self.get_next_proxy()

        # Sort by error count and success rate
        proxy = min(available_proxies, key=lambda p: (
            self.error_counts[self._get_proxy_key(p)],
            -self.success_counts[self._get_proxy_key(p)]
        ))

        # Create auth if needed
        auth = None
        if proxy.get('username') and proxy.get('password'):
            auth = aiohttp.BasicAuth(
                login=proxy['username'],
                password=proxy['password']
            )

        # Update last used time
        self.last_used[self._get_proxy_key(proxy)] = now
        
        return proxy, auth

    def mark_success(self, proxy: Dict[str, str]):
        """Mark a proxy as successful"""
        proxy_key = self._get_proxy_key(proxy)
        self.success_counts[proxy_key] += 1
        self.error_counts[proxy_key] = max(0, self.error_counts[proxy_key] - 1)  # Reduce error count on success

    def mark_error(self, proxy: Dict[str, str]):
        """Mark a proxy as failed"""
        proxy_key = self._get_proxy_key(proxy)
        self.error_counts[proxy_key] += 1
        
        # If too many errors, put proxy in cooldown
        if self.error_counts[proxy_key] >= self.max_errors:
            self.cooldown_until[proxy_key] = datetime.now() + timedelta(minutes=self.cooldown_minutes)
            logger.warning(f"Proxy {proxy['url']} placed in cooldown until {self.cooldown_until[proxy_key]}")
            self.error_counts[proxy_key] = 0  # Reset error count after cooldown

class LeadGenerator:
    def __init__(self):
        if not settings.is_ai_configured:
            raise ValueError("GROQ_API_KEY is not configured in environment variables")
            
        self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.results_dir = "lead_results"
        
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # Initialize proxy manager if proxies are configured
        self.proxy_manager = ProxyManager(settings.PROXY_URLS) if settings.is_proxy_configured else None
        if self.proxy_manager:
            logger.info(f"Initialized with {len(settings.PROXY_URLS)} proxies")
        else:
            logger.warning("No proxies configured - Google rate limiting may occur")

    async def process_icp_to_search_query(self, icp: str) -> List[str]:
        """Convert ICP description to multiple Google search queries using Groq AI"""
        try:
            logger.info("Generating search queries from ICP...")
            prompt = f"""
            Convert this Ideal Customer Profile description into 5 different Google search queries that will find LinkedIn profiles of matching people.
            Each query should use different combinations of terms to maximize results.
            Use LinkedIn's site search and relevant operators.
            
            ICP Description: {icp}
            
            Format each query like this example:
            site:linkedin.com/in/ (Job Title OR Alternative Title) AND (Industry OR Sector) AND (Location OR Region)
            
            Return exactly 5 different search queries, one per line, nothing else.
            Make each query unique by using different synonyms or combinations.
            """
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="mixtral-8x7b-32768",
                temperature=0.2,
            )
            
            queries = chat_completion.choices[0].message.content.strip().split('\n')
            # Ensure we have at least one query
            if not queries:
                return [f'site:linkedin.com/in/ {icp}']
            logger.info(f"Generated {len(queries)} search queries")
            return queries[:5]  # Limit to 5 queries
            
        except Exception as e:
            logger.error(f"Error in Groq AI processing: {str(e)}")
            # Fallback to basic query if AI processing fails
            return [f'site:linkedin.com/in/ {icp}']

    def is_valid_linkedin_profile_url(self, url: str) -> bool:
        """Validate if URL is a legitimate LinkedIn profile URL"""
        # Remove any query parameters
        base_url = url.split('?')[0].split('&')[0]
        
        # Basic validation rules
        if not base_url.startswith('https://www.linkedin.com/in/'):
            return False
            
        # Check if URL contains search operators (indicating it's a search URL)
        if any(operator in base_url for operator in ['OR', 'AND', '%20OR%20', '%20AND%20', '+OR+', '+AND+']):
            return False
            
        # Get the profile ID part
        profile_id = base_url.split('/in/')[-1].strip('/')
        
        # Profile ID should be reasonable length and not contain suspicious characters
        if len(profile_id) < 3 or len(profile_id) > 100 or '%' in profile_id:
            return False
            
        return True

    def extract_linkedin_url(self, google_url: str) -> str:
        """Extract clean LinkedIn profile URL from Google redirect URL"""
        try:
            # Find the LinkedIn URL portion
            if '/url?q=' in google_url:
                # Extract URL from Google redirect
                url = google_url.split('/url?q=')[1].split('&')[0]
                url = unquote(url)  # URL decode
            else:
                url = google_url
                
            # Ensure it starts with https://
            if url.startswith('//'):
                url = 'https:' + url
            elif not url.startswith('http'):
                url = 'https://' + url
                
            # Clean up the URL
            url = url.split('?')[0].split('&')[0]
            
            return url
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn URL: {str(e)}")
            return None

    async def make_request(self, session: aiohttp.ClientSession, url: str, headers: Dict[str, str]) -> Tuple[str, bool]:
        """Make a request with proxy rotation and error handling"""
        max_retries = 3
        current_retry = 0
        
        while current_retry < max_retries:
            if self.proxy_manager:
                proxy, auth = await self.proxy_manager.get_next_proxy()
                if not proxy:
                    logger.error("No proxies available")
                    raise ValueError("No proxies available")
                
                request_kwargs = {
                    'headers': headers,
                    'proxy': proxy['url']
                }
                if auth:
                    request_kwargs['proxy_auth'] = auth
                
                try:
                    async with session.get(url, **request_kwargs) as response:
                        if response.status == 200:
                            html = await response.text()
                            if "unusual traffic" not in html.lower() and "captcha" not in html.lower():
                                self.proxy_manager.mark_success(proxy)
                                return html, True
                        
                        self.proxy_manager.mark_error(proxy)
                        logger.warning(f"Request failed with proxy {proxy['url']}, status: {response.status}")
                        
                except Exception as e:
                    self.proxy_manager.mark_error(proxy)
                    logger.error(f"Error with proxy {proxy['url']}: {str(e)}")
            
            else:
                # No proxy available, make direct request
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            if "unusual traffic" not in html.lower() and "captcha" not in html.lower():
                                return html, True
                except Exception as e:
                    logger.error(f"Error making direct request: {str(e)}")
            
            current_retry += 1
            if current_retry < max_retries:
                await asyncio.sleep(random.uniform(1, 3))  # Random delay between retries
        
        return "", False

    async def scrape_linkedin_profiles(self, search_queries: List[str], num_leads: int, start_index: int = 0, seen_urls: Optional[Set[str]] = None) -> SearchResult:
        """Scrape LinkedIn profile URLs from Google search results"""
        profiles = []
        seen_urls = seen_urls if seen_urls is not None else set()  # Use provided set or create new one
        warnings = set()  # Use set to avoid duplicate warnings
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Configure timeout
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        max_pages = 20
        max_empty_pages = 2
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for query_index, search_query in enumerate(search_queries, 1):
                logger.info(f"Processing query {query_index}/{len(search_queries)} for profiles {start_index+1} to {start_index+num_leads}")
                if len(profiles) >= num_leads:
                    break
                    
                encoded_query = quote_plus(search_query)
                google_start_index = 0
                consecutive_empty_pages = 0
                reached_page_limit = False
                
                while len(profiles) < num_leads and consecutive_empty_pages < max_empty_pages:
                    google_url = f"https://www.google.com/search?q={encoded_query}&start={google_start_index}"
                    logger.info(f"Searching page {(google_start_index//10) + 1} for query {query_index}")
                    
                    html, success = await self.make_request(session, google_url, headers)
                    if not success:
                        warnings.add("Search request failed. Consider checking proxy configuration.")
                        break

                    # Check for end of results
                    if "did not match any documents" in html:
                        break

                    soup = BeautifulSoup(html, 'html.parser')
                    links = soup.find_all('a')
                    found_valid_links = False

                    for link in links:
                        href = link.get('href', '')
                        if 'linkedin.com/in/' in href:
                            linkedin_url = self.extract_linkedin_url(href)
                            
                            if linkedin_url and self.is_valid_linkedin_profile_url(linkedin_url):
                                if linkedin_url not in seen_urls:
                                    found_valid_links = True
                                    seen_urls.add(linkedin_url)
                                    
                                    profile_data = {
                                        'profile_url': linkedin_url,
                                        'name': '',  # Temporarily disabled
                                        'organization': '',  # Temporarily disabled
                                        'designation': '',  # Temporarily disabled
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    
                                    profiles.append(profile_data)
                                    logger.info(f"Found profile {start_index + len(profiles)}")
                                    
                                    if len(profiles) >= num_leads:
                                        break

                    if not found_valid_links:
                        consecutive_empty_pages += 1
                    else:
                        consecutive_empty_pages = 0
                    
                    # Move to next page
                    google_start_index += 10
                    
                    # Check if we've reached page limit
                    if google_start_index >= max_pages * 10:
                        reached_page_limit = True
                        break
                
                if reached_page_limit and len(profiles) < num_leads:
                    warnings.add(f"Reached maximum page limit ({max_pages} pages) for search query {query_index}.")
        
        # Only add exhausted warning if we didn't find enough profiles
        if len(profiles) < num_leads:
            warnings.add(f"Found {len(profiles)} profiles out of {num_leads} requested from available search results.")
        
        return SearchResult(profiles, len(profiles), list(warnings))

    async def generate_leads(self, icp: str, num_leads: int, start_index: int = 0, seen_urls: Optional[Set[str]] = None, search_queries: Optional[List[str]] = None) -> Tuple[str, str]:
        """Main method to generate leads. Returns tuple of (filepath, message)"""
        try:
            logger.info(f"Starting lead generation for ICP: {icp[:50]}... (profiles {start_index+1} to {start_index+num_leads})")
            
            # Use provided search queries or generate new ones
            if not search_queries:
                search_queries = await self.process_icp_to_search_query(icp)
            
            # Log which queries this task will use
            logger.info(f"Using {len(search_queries)} search queries for this task")
            for i, query in enumerate(search_queries, 1):
                logger.info(f"Query {i}: {query}")
            
            # Scrape profiles using the queries
            search_result = await self.scrape_linkedin_profiles(search_queries, num_leads, start_index, seen_urls)
            
            # Always save whatever profiles we found
            if search_result.profiles:
                # Generate unique filename with ICP summary and range
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Create a short summary from ICP (first 30 chars)
                icp_summary = icp.replace(" ", "_")[:30].lower()
                filename = f"ICP_{icp_summary}_{start_index+1}_to_{start_index+len(search_result.profiles)}_{timestamp}.csv"
                filepath = os.path.join(self.results_dir, filename)
                
                # Save results to CSV with new fields
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['profile_url', 'name', 'organization', 'designation', 'timestamp'])
                    writer.writeheader()
                    writer.writerows(search_result.profiles)
                
                logger.info(f"Lead generation completed. Found {len(search_result.profiles)} profiles.")
                
                # Create appropriate message based on results
                if search_result.total_found >= num_leads:
                    message = f"Successfully found {search_result.total_found} profiles."
                else:
                    message = "; ".join(search_result.warnings) if search_result.warnings else "No additional information."
                
                return filepath, message
            else:
                raise ValueError("No profiles found in search results.")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in lead generation: {error_message}")
            raise ValueError(error_message)
