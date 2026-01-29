import requests
from bs4 import BeautifulSoup
import trafilatura
from fake_useragent import UserAgent
import random
import time
from typing import List, Dict, Optional
import asyncio


class WebScraper:
    """
    Handles searching the web and simple content extraction.
    Uses DuckDuckGo HTML (no API key required) and Trafilatura.
    """
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Generates random headers to mimic a real browser."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }

    def search_web(self, query: str, num_results: int = 3) -> List[str]:
        """
        Performs a search (DuckDuckGo HTML) and returns a list of URLs.
        """
        print(f"searching for: {query}")
        search_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}
        
        try:
            # Sleep briefly to avoid instant blocks between sequential calls
            time.sleep(random.uniform(1.0, 2.5))
            
            resp = self.session.post(search_url, data=data, headers=self._get_headers(), timeout=10)
            if resp.status_code != 200:
                print(f"error: search failed with status {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = []
            
            # DuckDuckGo HTML structure extraction
            # Class names may change, this is a common scraping fragility
            for link in soup.find_all('a', class_='result__a'):
                href = link.get('href')
                if href and 'duckduckgo.com/l/?' not in href: # Filter out tracking redirects if possible
                    urls.append(href)
            
            # Fallback strategy if specific class not found
            if not urls:
                links = [a['href'] for a in soup.find_all('a', href=True) if 'http' in a['href']]
                urls = [l for l in links if 'duckduckgo' not in l and 'microsoft' not in l]

            return urls[:num_results]

        except Exception as e:
            print(f"error: search exception: {e}")
            return []

    def extract_content(self, url: str) -> Dict[str, str]:
        """
        Downloads and parses the main text content from a URL using Trafilatura.
        """
        print(f"scraping content: {url}")
        try:
            # Trafilatura handles the request and extraction
            downloaded = trafilatura.fetch_url(url)
            
            if downloaded is None:
                return {"url": url, "error": "Empty response/timeout", "status": "failed"}
            
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
            print(f"error: extraction error for {url}: {e}")
            return {"url": url, "error": str(e), "status": "failed"}

# Standalone function for simpler usage in the pipeline
async def scrape_company_data(company_name: str, cin: Optional[str] = None) -> Dict:
    """
    Main pipeline function for scraping.
    1. Defines search queries (Reputation, Scam checks).
    2. Searches the web.
    3. Extracts content.
    """
    scraper = WebScraper()
    
    # 1. define search queries
    # we focus on reputation and legitimacy signals
    queries = [
        f"{company_name} reviews",
        f"{company_name} real or fake",
        f"{company_name} scam complaints"
    ]
    
    if cin:
        queries.append(f"{cin} company information")
    
    all_urls = []
    
    # 2. run searches
    # using a simple loop. for production, consider asyncio.gather with rate limiting.
    for q in queries:
        urls = scraper.search_web(q, num_results=2)
        all_urls.extend(urls)
        
    # deduplicate urls
    unique_urls = list(set(all_urls))
    print(f"found {len(unique_urls)} unique urls to process")
    
    # 3. extract content from each url
    results = []
    for url in unique_urls:
        data = scraper.extract_content(url)
        # filter out empty or failed scrapes
        if data['status'] == 'success' and len(data.get('text', '')) > 50:
             results.append(data)
    
    return {
        "company_name": company_name,
        "scraped_sources_count": len(results),
        "sources": results
    }
