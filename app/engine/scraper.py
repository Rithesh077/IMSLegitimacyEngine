import requests
from bs4 import BeautifulSoup
import trafilatura
from fake_useragent import UserAgent
import random
import time
from typing import List, Dict, Optional, Any
from thefuzz import fuzz

class WebScraper:
    """Robust web search and content extraction using DuckDuckGo and randomized headers."""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        # TODO: Configure proper logging level for urllib3 in prod
        # logging.getLogger("urllib3").setLevel(logging.WARNING)

    def _get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }

    def search_web(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        # logger.info(f"search: {query}")
        search_url = "https://html.duckduckgo.com/html/"
        data = {'q': query}
        
        for attempt in range(3):
            try:
                # exponential backoff
                delay = random.uniform(2.0, 5.0) + (1.5 * attempt)
                time.sleep(delay)
                
                resp = self.session.post(search_url, data=data, headers=self._get_headers(), timeout=30)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = []
                    
                    result_blocks = soup.find_all('div', class_='result__body')
                    if not result_blocks:
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
                            link_href = title_tag.get('href', '') if title_tag else ''
                            snippet_tag = block.find('a', class_='result__snippet')
                            
                            if link_href and 'duckduckgo.com/l/?' not in link_href:
                                results.append({
                                    'title': title_tag.get_text(strip=True),
                                    'link': link_href,
                                    'snippet': snippet_tag.get_text(strip=True) if snippet_tag else ''
                                })
                    return results[:num_results]
                
            except Exception:
                pass
        
        return []

    def extract_content(self, url: str) -> Dict[str, str]:
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            if response.status_code != 200:
                 return {"url": url, "error": f"Status {response.status_code}", "status": "failed"}

            downloaded = response.text
            text = trafilatura.extract(downloaded, include_comments=True, include_tables=False, favor_precision=True)
            metadata = trafilatura.extract_metadata(downloaded)
            
            return {
                "url": url,
                "title": metadata.title if metadata and metadata.title else "Unknown",
                "text": text if text else "",
                "status": "success"
            }
        except Exception as e:
            return {"url": url, "error": str(e), "status": "failed"}

    def verify_url_owner(self, url: str, expected_name: str) -> bool:
        # reverse lookup the url to see if title matches expected name
        results = self.search_web(url, num_results=3)
        if not results: return False
        
        top = results[0]
        score = self.calculate_fuzzy_match(expected_name, top.get('title', ''))
        return score > 70

    def calculate_fuzzy_match(self, str1: str, str2: str) -> int:
        return fuzz.token_set_ratio(str1.lower(), str2.lower())

    def perform_reputation_search(self, company_name: str) -> List[Dict[str, str]]:
        queries = [
            f"{company_name} reviews",
            f"{company_name} scam fraud complaint",
            f"{company_name} employee reviews"
        ]
        
        aggregated = []
        seen = set()
        
        for q in queries:
            results = self.search_web(q, num_results=3)
            for res in results:
                if res['link'] not in seen:
                    seen.add(res['link'])
                    aggregated.append(res)
                    
        return aggregated

    def verify_association(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """
        Verifies if entity2 is associated with entity1 via web search.
        Returns: { verified: bool, score: int, source: str }
        """
        query = f'{entity1} {entity2}'
        print(f"Verifying association: {query}")
        results = self.search_web(query, num_results=5)
        
        best_score = 0
        best_source = ""
        
        for res in results:
            text = (res.get('title', '') + " " + res.get('snippet', '')).lower()
            
            # Check if both entities appear in the text
            # We use fuzzy partial match for robustness
            s1 = fuzz.partial_token_set_ratio(entity1.lower(), text)
            s2 = fuzz.partial_token_set_ratio(entity2.lower(), text)
            
            # Combined confidence: both must be present
            if s1 > 80 and s2 > 80:
                avg_score = (s1 + s2) // 2
                if avg_score > best_score:
                    best_score = avg_score
                    best_source = res.get('link')

        return {
            "verified": best_score > 75,
            "score": best_score,
            "source": best_source
        }
