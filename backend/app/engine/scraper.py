import requests
from bs4 import BeautifulSoup
import trafilatura
from fake_useragent import UserAgent
import random
import time
from typing import List, Dict, Optional
from thefuzz import fuzz

class WebScraper:
    """
    Handles robust web search and content extraction.
    Utilizes DuckDuckGo HTML endpoint and randomized user agents to ensure reliability.
    """
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Returns randomized headers to mimic a legitimate browser."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }

    def search_web(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        """
        Performs a web search via DuckDuckGo HTML.
        Includes exponential backoff and randomized delays to respect rate limits.
        """
        print(f"Executing search: {query}")
        search_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}
        
        for attempt in range(3):
            try:
                # Politeness delay to prevent blocking
                delay = random.uniform(3.0, 6.0)
                if attempt > 0: delay += 2.0 * attempt # Exponential backoff
                time.sleep(delay)
                
                resp = self.session.post(search_url, data=data, headers=self._get_headers(), timeout=30)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = []
                    
                    # Parse DuckDuckGo HTML structure
                    result_blocks = soup.find_all('div', class_='result__body')
                    if not result_blocks:
                        # Fallback parsing strategy
                        links = soup.find_all('a', class_='result__a')
                        for link in links:
                            results.append({
                                'title': link.get_text(strip=True),
                                'link': link.get('href'),
                                'snippet': ''
                            })
                    else:
                        for block in result_blocks:
                            title_tag = block.find('a', class_='result__a')
                            snippet_tag = block.find('a', class_='result__snippet')
                            if title_tag:
                                href = title_tag.get('href', '')
                                if 'duckduckgo.com/l/?' not in href: 
                                    results.append({
                                        'title': title_tag.get_text(strip=True),
                                        'link': href,
                                        'snippet': snippet_tag.get_text(strip=True) if snippet_tag else ''
                                    })
                    return results[:num_results]
                
                elif resp.status_code == 403:
                    print(f"Warning: 403 Forbidden. Retrying...")
                else:
                    print(f"Warning: Unexpected status {resp.status_code}. Retrying...")
                    
            except Exception as e:
                print(f"Search attempt {attempt+1} failed: {e}")
        
        print("Search failed after all retries.")
        return []

    def extract_content(self, url: str) -> Dict[str, str]:
        """Extacts main content text from a given URL using Trafilatura."""
        print(f"Extracting content: {url}")
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            if response.status_code != 200:
                 return {"url": url, "error": f"Status {response.status_code}", "status": "failed"}

            downloaded = response.text
             
            text = trafilatura.extract(downloaded, include_comments=True, include_tables=False, favor_precision=True)
            metadata = trafilatura.extract_metadata(downloaded)
            
            title = metadata.title if metadata and metadata.title else "Unknown Title"
            
            return {
                "url": url,
                "title": title,
                "text": text if text else "",
                "status": "success"
            }
        except Exception as e:
            print(f"Extraction error for {url}: {e}")
            return {"url": url, "error": str(e), "status": "failed"}

    def get_verification_context(self, query: str) -> str:
        """Retrieves context snippets for validation purposes."""
        results = self.search_web(query, num_results=5)
        context = []
        for res in results:
            context.append(f"Result: {res['title']} ({res['link']})")
            
        return "\n".join(context)

    def check_content_match(self, url: str, text_to_find: str) -> bool:
        """Verifies if specific text exists within the page content."""
        print(f"Verifying existence of '{text_to_find}' in {url}")
        data = self.extract_content(url)
        if data['status'] == 'success':
            haystack = (data.get('title', '') + " " + data.get('text', '')).lower()
            return text_to_find.lower() in haystack
        return False

    def calculate_fuzzy_match(self, str1: str, str2: str) -> int:
        """Calculates token-based fuzzy match score (0-100)."""
        return fuzz.token_set_ratio(str1.lower(), str2.lower())

    def verify_url_owner(self, url: str, expected_name: str) -> bool:
        """
        Reverse lookup to verify if a URL corresponds to the expected entity.
        Uses fuzzy matching on the search result title.
        """
        print(f"Verifying ownership of {url} for '{expected_name}'")
        
        results = self.search_web(url, num_results=3)
        if not results:
            return False
            
        top_result = results[0]
        title = top_result.get('title', '')
        
        score = self.calculate_fuzzy_match(expected_name, title)
        print(f"Fuzzy Match Score: {score}")
        
        # Threshold > 70 generally indicates a strong match
        if score > 70:
            print(f"Ownership Verified ({score})")
            return True
             
        print(f"Ownership Verification Failed ({score})")
        return False
