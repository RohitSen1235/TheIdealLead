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

# Configure logging - only show warnings and errors
logging.basicConfig(level=logging.WARNING)
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
        self.error_counts[proxy_key] = max(0, self.error_counts[proxy_key] - 1)

    def mark_error(self, proxy: Dict[str, str]):
        """Mark a proxy as failed"""
        proxy_key = self._get_proxy_key(proxy)
        self.error_counts[proxy_key] += 1
        
        if self.error_counts[proxy_key] >= self.max_errors:
            self.cooldown_until[proxy_key] = datetime.now() + timedelta(minutes=self.cooldown_minutes)
            self.error_counts[proxy_key] = 0

class LeadGenerator:
    def __init__(self):
        if not settings.is_ai_configured:
            raise ValueError("GROQ_API_KEY is not configured in environment variables")
            
        self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.results_dir = "lead_results"
        
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        self.proxy_manager = ProxyManager(settings.PROXY_URLS) if settings.is_proxy_configured else None

    async def get_complexity_multiple(self, icp: str) -> float:
        """Get complexity multiple from Groq AI based on ICP keywords"""
        try:
            prompt = f"""
            Return ONLY a whole number between 10 and 50 to represent the complexity of these ICP keywords. No text, no explanations, just the number.

            ICP: {icp}

            Guide for scoring:
            - 10-15: simple, commonly used keywords
            - 15-20: moderately specific terms
            - 20-30: slightly complex terms 
            - 30-40: industry-specific or technical terms
            - 40-50: combination of highly niche terms or specific industry or technical terms 
            """
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.6,
            )
            
            # Extract and validate the number
            response_text = chat_completion.choices[0].message.content.strip()
            
            # Remove any non-numeric characters
            cleaned_response = ''.join(c for c in response_text if c.isdigit())
            
            try:
                # Convert to integer first
                complexity_int = int(cleaned_response)
                # Ensure the number is within bounds
                complexity_int = max(10, min(50, complexity_int))
                # Convert to float by dividing by 10
                return complexity_int / 10.0
                
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse complexity multiple from AI response: {response_text}")
                logger.error(f"Parsing error: {str(e)}")
                return 1.0  # Default to 1.0 if parsing fails
                
        except Exception as e:
            logger.error(f"Error getting complexity multiple: {str(e)}")
            return 1.0  # Default to 1.0 on error

    async def calculate_credits(self, icp: str, num_leads: int, get_work_email: bool = False, get_phone_number: bool = False) -> Dict[str, float]:
        """Calculate the number of credits required for lead generation"""
        # Get complexity multiple
        complexity_multiple = await self.get_complexity_multiple(icp)
        
        # Base credits per lead adjusted by complexity
        base_credits = num_leads * settings.BASE_CREDITS_PER_LEAD * complexity_multiple
        
        # Credits for AI processing (for generating search queries)
        ai_credits = num_leads * settings.AI_QUERY_CREDITS
        
        # Additional credits for optional services
        work_email_credits = num_leads * settings.BASE_CREDITS_PER_LEAD * 2 if get_work_email else 0
        phone_number_credits = num_leads * settings.BASE_CREDITS_PER_LEAD * 3 if get_phone_number else 0
        
        # Total credits required
        total_credits = base_credits + ai_credits + work_email_credits + phone_number_credits
        
        return {
            "base_credits": round(base_credits, 1),
            "ai_credits": ai_credits,
            "work_email_credits": work_email_credits,
            "phone_number_credits": phone_number_credits,
            "total_credits": round(total_credits, 1),
            "complexity_multiple": complexity_multiple,
            "breakdown": {
                "per_lead": settings.BASE_CREDITS_PER_LEAD,
                "ai_processing": settings.AI_QUERY_CREDITS,
                "work_email_cost": settings.BASE_CREDITS_PER_LEAD * 2 if get_work_email else 0,
                "phone_number_cost": settings.BASE_CREDITS_PER_LEAD * 3 if get_phone_number else 0,
                "number_of_leads": num_leads
            }
        }

    async def get_work_email(self, name: str, company: str) -> Optional[str]:
        """Use AI to generate dummy work email based on name and company for development"""
        try:
            prompt = f"""
            Generate the most likely work email for this person based on their name and company.
            Use common email patterns (e.g., first.last@company.com, firstinitiallast@company.com).
            Return only the email address, nothing else.

            Name: {name}
            Company: {company}
            """
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.1,
            )
            
            email = chat_completion.choices[0].message.content.strip()
            return email if '@' in email else None
            
        except Exception as e:
            logger.error(f"Error generating work email: {str(e)}")
            return None

    async def get_phone_number(self, name: str, company: str) -> Optional[str]:
        """Use AI to generate dummy business phone number"""
        try:
            prompt = f"""
            Generate a plausible business phone number for this person.
            Use standard US format (XXX-XXX-XXXX).
            Return only the phone number, nothing else.

            """
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.1,
            )
            
            phone = chat_completion.choices[0].message.content.strip()
            # Basic validation for phone number format
            if len(phone.replace('-', '')) == 10 and phone.count('-') == 2:
                return phone
            return None
            
        except Exception as e:
            logger.error(f"Error generating phone number: {str(e)}")
            return None

    async def process_icp_to_search_query(self, icp: str) -> List[str]:
        """Convert ICP description to exactly 5 LinkedIn search queries using Groq AI"""
        try:
            prompt = f"""
            Convert this Ideal Customer Profile description into exactly 5 different LinkedIn search queries.
            Each query should use different combinations of terms to maximize unique results.
            
            ICP Description: {icp}
            
            Format each query like this:
            site:linkedin.com/in/ (Job Title OR Alternative Title) AND (Industry OR Company)
            
            Return exactly 5 different search queries, one per line, nothing else.
            Make each query unique by using different synonyms or combinations.
            """
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.2,
            )
            
            queries = chat_completion.choices[0].message.content.strip().split('\n')
            
            # Ensure exactly 5 queries
            if len(queries) < 5:
                # Add basic queries if needed
                base_query = f'site:linkedin.com/in/ {icp}'
                while len(queries) < 5:
                    queries.append(base_query)
            
            return queries[:5]  # Return exactly 5 queries
            
        except Exception as e:
            logger.error(f"Error in Groq AI processing: {str(e)}")
            # Fallback to 5 basic queries
            base_query = f'site:linkedin.com/in/ {icp}'
            return [base_query] * 5

    def is_valid_linkedin_profile_url(self, url: str) -> bool:
        """Validate if URL is a legitimate LinkedIn profile URL"""
        # Remove any query parameters and fragments
        base_url = url.split('?')[0].split('#')[0].lower()
        
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

    def extract_linkedin_url(self, google_url: str) -> Optional[str]:
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
            
            return url if self.is_valid_linkedin_profile_url(url) else None
            
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
                        
                except Exception as e:
                    self.proxy_manager.mark_error(proxy)
            
            else:
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            if "unusual traffic" not in html.lower() and "captcha" not in html.lower():
                                return html, True
                except Exception as e:
                    pass
            
            current_retry += 1
            if current_retry < max_retries:
                await asyncio.sleep(random.uniform(1, 3))
        
        return "", False

    async def scrape_linkedin_profiles(self, search_queries: List[str], num_leads: int, start_index: int = 0, seen_urls: Optional[Set[str]] = None) -> SearchResult:
        """Scrape LinkedIn profile URLs from Google search results"""
        profiles = []
        seen_urls = seen_urls if seen_urls is not None else set()
        warnings = set()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        timeout = aiohttp.ClientTimeout(total=30)
        max_pages = int((num_leads/2.5) + 1)  # Calculate max_pages based on required leads
        max_empty_pages = 2
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for search_query in search_queries:
                if len(profiles) >= num_leads:
                    break
                    
                encoded_query = quote_plus(search_query)
                google_start_index = 0
                consecutive_empty_pages = 0
                reached_page_limit = False
                
                while len(profiles) < num_leads and consecutive_empty_pages < max_empty_pages:
                    google_url = f"https://www.google.com/search?q={encoded_query}&start={google_start_index}"
                    
                    html, success = await self.make_request(session, google_url, headers)
                    if not success:
                        warnings.add("Search request failed. Consider checking proxy configuration.")
                        break

                    if "did not match any documents" in html:
                        break

                    soup = BeautifulSoup(html, 'html.parser')
                    links = soup.find_all('a')
                    found_valid_links = False

                    for link in links:
                        href = link.get('href', '')
                        if 'linkedin.com/in/' in href:
                            linkedin_url = self.extract_linkedin_url(href)
                            
                            if linkedin_url and linkedin_url not in seen_urls:
                                found_valid_links = True
                                seen_urls.add(linkedin_url)
                                
                                profile_data = {
                                    'profile_url': linkedin_url,
                                    'name': '',
                                    'organization': '',
                                    'designation': '',
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                profiles.append(profile_data)
                                
                                if len(profiles) >= num_leads:
                                    break

                    if not found_valid_links:
                        consecutive_empty_pages += 1
                    else:
                        consecutive_empty_pages = 0
                    
                    google_start_index += 10
                    
                    if google_start_index >= max_pages * 10:
                        reached_page_limit = True
                        break
                
                if reached_page_limit and len(profiles) < num_leads:
                    warnings.add(f"Reached maximum page limit ({max_pages} pages) for search query.")
        
        if len(profiles) < num_leads:
            warnings.add(f"Found {len(profiles)} profiles out of {num_leads} requested from available search results.")
        
        return SearchResult(profiles, len(profiles), list(warnings))

    async def generate_leads(self, icp: str, num_leads: int, get_work_email: bool = False, get_phone_number: bool = False, start_index: int = 0, seen_urls: Optional[Set[str]] = None, search_queries: Optional[List[str]] = None) -> Tuple[str, str]:
        """Main method to generate leads from LinkedIn with optional services"""
        try:
            # First attempt with initial search queries
            if not search_queries:
                search_queries = await self.process_icp_to_search_query(icp)
            
            search_result = await self.scrape_linkedin_profiles(search_queries, num_leads, start_index, seen_urls)
            
            # If no profiles found, try one more time with new search queries
            if not search_result.profiles:
                logger.warning("No profiles found in first attempt. Trying with new search queries...")
                new_search_queries = await self.process_icp_to_search_query(icp)
                search_result = await self.scrape_linkedin_profiles(new_search_queries, num_leads, start_index, seen_urls)
            
            if search_result.profiles:
                # Add optional services data
                if get_work_email or get_phone_number:
                    for profile in search_result.profiles:
                        if get_work_email:
                            profile['work_email'] = await self.get_work_email(profile['name'], profile['organization'])
                        if get_phone_number:
                            profile['phone_number'] = await self.get_phone_number(profile['name'], profile['organization'])
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                icp_summary = icp.replace(" ", "_")[:30].lower()
                filename = f"ICP_{icp_summary}_{start_index+1}_to_{start_index+len(search_result.profiles)}_{timestamp}.csv"
                filepath = os.path.join(self.results_dir, filename)
                
                fieldnames = ['profile_url', 'name', 'organization', 'designation', 'timestamp']
                if get_work_email:
                    fieldnames.append('work_email')
                if get_phone_number:
                    fieldnames.append('phone_number')
                
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(search_result.profiles)
                
                if search_result.total_found >= num_leads:
                    message = f"Successfully found {search_result.total_found} profiles."
                else:
                    message = "; ".join(search_result.warnings) if search_result.warnings else "No additional information."
                
                return filepath, message
            else:
                # Create empty results file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                icp_summary = icp.replace(" ", "_")[:30].lower()
                filename = f"ICP_{icp_summary}_no_results_{timestamp}.csv"
                filepath = os.path.join(self.results_dir, filename)
                
                fieldnames = ['profile_url', 'name', 'organization', 'designation', 'timestamp']
                if get_work_email:
                    fieldnames.append('work_email')
                if get_phone_number:
                    fieldnames.append('phone_number')
                
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                
                return filepath, "No profiles found after retrying with new search queries."
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in lead generation: {error_message}")
            raise ValueError(error_message)
