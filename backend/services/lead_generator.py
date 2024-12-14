import asyncio
from typing import List, Tuple
import aiohttp
from bs4 import BeautifulSoup
import os
import csv
from datetime import datetime
import groq
from urllib.parse import quote_plus, unquote
import json
from config import settings

class LeadGenerator:
    def __init__(self):
        if not settings.is_ai_configured:
            raise ValueError("GROQ_API_KEY is not configured in environment variables")
            
        self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.results_dir = "lead_results"
        
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    async def process_icp_to_search_query(self, icp: str) -> List[str]:
        """Convert ICP description to multiple Google search queries using Groq AI"""
        try:
            prompt = f"""
            Convert this Ideal Customer Profile description into 3 different Google search queries that will find LinkedIn profiles of matching people.
            Each query should use different combinations of terms to maximize results.
            Use LinkedIn's site search and relevant operators.
            
            ICP Description: {icp}
            
            Format each query like this example:
            site:linkedin.com/in/ (Job Title OR Alternative Title) AND (Industry OR Sector) AND (Location OR Region)
            
            Return exactly 3 different search queries, one per line, nothing else.
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
                temperature=0.3,
            )
            
            queries = chat_completion.choices[0].message.content.strip().split('\n')
            # Ensure we have at least one query
            if not queries:
                return [f'site:linkedin.com/in/ {icp}']
            return queries[:3]  # Limit to 3 queries
            
        except Exception as e:
            print(f"Error in Groq AI processing: {str(e)}")
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
            print(f"Error extracting LinkedIn URL: {str(e)}")
            return None

    async def scrape_linkedin_profiles(self, search_queries: List[str], num_leads: int) -> Tuple[List[dict], str]:
        """Scrape LinkedIn profiles from Google search results with pagination. Returns (profiles, reason)"""
        profiles = []
        seen_urls = set()  # Track seen URLs to avoid duplicates
        stop_reason = ""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            for query_index, search_query in enumerate(search_queries, 1):
                if len(profiles) >= num_leads:
                    break
                    
                encoded_query = quote_plus(search_query)
                start_index = 0
                consecutive_empty_pages = 0
                
                while len(profiles) < num_leads and consecutive_empty_pages < 3:
                    google_url = f"https://www.google.com/search?q={encoded_query}&start={start_index}"
                    
                    try:
                        # Add delay between requests to avoid rate limiting
                        await asyncio.sleep(2)
                        
                        async with session.get(google_url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                
                                # Check for Google rate limiting or blocking
                                if "unusual traffic" in html.lower() or "captcha" in html.lower():
                                    stop_reason = "Google's security check was triggered. This usually happens when making too many requests."
                                    break
                                
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Check if we've hit the last page
                                if "did not match any documents" in html:
                                    if start_index == 0:
                                        stop_reason = f"No search results found for query variation {query_index}."
                                    else:
                                        stop_reason = f"Reached end of search results for query variation {query_index}."
                                    break
                                
                                # Find all search result links
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
                                                profiles.append({
                                                    'profile_url': linkedin_url,
                                                    'timestamp': datetime.now().isoformat()
                                                })
                                                
                                                if len(profiles) >= num_leads:
                                                    break
                                
                                if not found_valid_links:
                                    consecutive_empty_pages += 1
                                else:
                                    consecutive_empty_pages = 0
                                
                                # Move to next page
                                start_index += 10
                            else:
                                stop_reason = f"Received HTTP {response.status} error from Google. Search stopped."
                                break
                                
                    except Exception as e:
                        stop_reason = f"Error during search: {str(e)}"
                        break
                        
                    # Break if we've gone through too many pages
                    if start_index > 100:  # Limit to 10 pages
                        stop_reason = "Reached maximum page limit for the current search query."
                        break
                
                # If we hit a rate limit, stop trying more queries
                if "security check" in stop_reason.lower():
                    break
        
        # Determine final reason if we haven't found any profiles
        if len(profiles) == 0 and not stop_reason:
            stop_reason = "No matching LinkedIn profiles found in any of the search queries."
        # Or if we found some but not enough
        elif len(profiles) < num_leads:
            if not stop_reason:
                stop_reason = "Exhausted all available search results."
            stop_reason = f"Found {len(profiles)} profiles out of {num_leads} requested. {stop_reason}"
            
        return profiles, stop_reason

    async def generate_leads(self, icp: str, num_leads: int) -> Tuple[str, str]:
        """Main method to generate leads. Returns tuple of (filepath, message)"""
        try:
            # Convert ICP to multiple search queries
            search_queries = await self.process_icp_to_search_query(icp)
            
            # Scrape profiles using multiple queries
            profiles, stop_reason = await self.scrape_linkedin_profiles(search_queries, num_leads)
            
            # Always save whatever profiles we found
            if profiles:
                # Generate unique filename with ICP summary
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # Create a short summary from ICP (first 30 chars)
                icp_summary = icp.replace(" ", "_")[:30].lower()
                filename = f"ICP_{icp_summary}_{timestamp}.csv"
                filepath = os.path.join(self.results_dir, filename)
                
                # Save results to CSV
                with open(filepath, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['profile_url', 'timestamp'])
                    writer.writeheader()
                    writer.writerows(profiles)
                
                return filepath, stop_reason
            else:
                raise ValueError(stop_reason)
            
        except Exception as e:
            error_message = str(e)
            print(f"Error in lead generation: {error_message}")
            raise ValueError(error_message)
