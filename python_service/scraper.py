import requests
from bs4 import BeautifulSoup
import trafilatura
from fake_useragent import UserAgent
import random
import time
from typing import List, Dict

class WebScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()

    def _get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }

    def search_web(self, query: str, num_results: int = 5) -> List[str]:
        """
        Performs a search (DuckDuckGo HTML to avoid harsh Google rate limits) 
        and returns a list of URLs.
        """
        print(f"Searching for: {query}")
        search_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}
        
        try:
            # Sleep briefly to avoid instant blocks between calls
            time.sleep(random.uniform(1, 2))
            
            resp = self.session.post(search_url, data=data, headers=self._get_headers(), timeout=10)
            if resp.status_code != 200:
                print(f"Search failed: {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = []
            
            # DuckDuckGo HTML structure usually has results in 'result__a'
            for link in soup.find_all('a', class_='result__a'):
                href = link.get('href')
                if href and 'duckduckgo.com/l/?' not in href: # Direct link
                    urls.append(href)
                elif href: # Redirect link, extract actual url
                    # Simple extraction or decoding could go here if needed
                    pass
            
            # Additional fallback for parsing generic result links if class names change
            if not urls:
                links = [a['href'] for a in soup.find_all('a', href=True) if 'http' in a['href']]
                # Filter out garbage
                urls = [l for l in links if 'duckduckgo' not in l and 'microsoft' not in l]

            return urls[:num_results]

        except Exception as e:
            print(f"Search Error: {e}")
            return []

    def extract_content(self, url: str) -> Dict[str, str]:
        """
        Downloads and parses the main text content from a URL using Trafilatura.
        """
        print(f"Scraping: {url}")
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded is None:
                return {"url": url, "error": "Empty response"}
            
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            metadata = trafilatura.extract_metadata(downloaded)
            
            title = metadata.title if metadata else "Unknown Title"
            
            return {
                "url": url,
                "title": title,
                "text": text if text else "",
                "status": "success"
            }
        except Exception as e:
            print(f"Extraction Error for {url}: {e}")
            return {"url": url, "error": str(e), "status": "failed"}

# Quick Test
if __name__ == "__main__":
    scraper = WebScraper()
    links = scraper.search_web("Zomato legit output", 3)
    print("Links Found:", links)
    for link in links:
        data = scraper.extract_content(link)
        print(f"--- {data.get('title')} ---")
        print(data.get('text')[:200] + "...")
