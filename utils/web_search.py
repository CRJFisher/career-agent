"""
Web search utility using browser automation.

This module provides web search functionality through AI-driven browser automation,
supporting Google search with result extraction and relevance scoring.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
except ImportError:
    raise ImportError("Playwright is required. Install with: pip install playwright && playwright install")

from bs4 import BeautifulSoup

from utils.llm_wrapper import get_default_llm_wrapper

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, title: str, url: str, snippet: str, position: int):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.position = position
        self.relevance_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "position": self.position,
            "relevance_score": self.relevance_score
        }


class WebSearcher:
    """Browser-based web search implementation."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.llm = get_default_llm_wrapper()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()
    
    async def start_browser(self):
        """Initialize browser instance."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            logger.info(f"Browser started (headless={self.headless})")
    
    async def close_browser(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            logger.info("Browser closed")
    
    async def search(
        self, 
        query: str, 
        max_results: int = 10,
        score_relevance: bool = True
    ) -> List[SearchResult]:
        """
        Perform Google search and extract results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            score_relevance: Whether to score results for relevance
            
        Returns:
            List of SearchResult objects
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Use 'async with WebSearcher()' or call start_browser()")
        
        page = await self.browser.new_page()
        results = []
        
        try:
            # Navigate to Google
            search_url = f"https://www.google.com/search?q={quote_plus(query)}"
            await page.goto(search_url, wait_until='networkidle')
            
            # Wait for results to load
            await page.wait_for_selector('#search', timeout=10000)
            
            # Extract results
            results = await self._extract_results(page, max_results)
            
            # Score relevance if requested
            if score_relevance and results:
                results = await self._score_relevance(query, results)
            
            logger.info(f"Found {len(results)} results for query: {query}")
            
        except PlaywrightTimeout:
            logger.error(f"Timeout waiting for search results: {query}")
            await self._take_screenshot(page, "timeout_error.png")
        except Exception as e:
            logger.error(f"Error during search: {e}")
            await self._take_screenshot(page, "search_error.png")
        finally:
            await page.close()
        
        return results
    
    async def _extract_results(self, page: Page, max_results: int) -> List[SearchResult]:
        """Extract organic search results from the page."""
        results = []
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find organic results (skip ads)
        # Google's structure: div.g contains organic results
        result_divs = soup.select('div.g')
        
        for i, div in enumerate(result_divs[:max_results]):
            try:
                # Extract title
                title_elem = div.select_one('h3')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # Extract URL
                link_elem = div.select_one('a')
                if not link_elem or not link_elem.get('href'):
                    continue
                url = link_elem['href']
                
                # Extract snippet
                snippet_elem = div.select_one('div[data-sncf="1"], div[data-sncf="2"], span.aCOpRe')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Skip if it looks like an ad or sponsored content
                if self._is_ad(div):
                    continue
                
                result = SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    position=len(results) + 1
                )
                results.append(result)
                
            except Exception as e:
                logger.debug(f"Error extracting result {i}: {e}")
                continue
        
        return results
    
    def _is_ad(self, div) -> bool:
        """Check if a result div is an ad or sponsored content."""
        # Check for common ad indicators
        ad_indicators = ['sponsored', 'ad', 'ads']
        div_text = div.get_text(strip=True).lower()
        
        for indicator in ad_indicators:
            if indicator in div_text:
                return True
        
        # Check for ad-specific classes or attributes
        if div.select('[data-hveid*="CA"]'):  # Common ad identifier
            return True
            
        return False
    
    async def _score_relevance(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Score results for relevance using LLM."""
        # Create a batch scoring prompt
        prompt = f"""Score the relevance of these search results to the query: "{query}"

For each result, provide a relevance score from 0.0 to 1.0.
- 1.0 = Highly relevant, directly answers the query
- 0.5 = Moderately relevant, related but not direct
- 0.0 = Not relevant

Results:
"""
        
        for i, result in enumerate(results):
            prompt += f"\n{i+1}. Title: {result.title}\n   URL: {result.url}\n   Snippet: {result.snippet}\n"
        
        prompt += "\nProvide scores in format: 1:0.9, 2:0.7, 3:0.5, etc."
        
        try:
            response = await asyncio.to_thread(self.llm.call_llm_sync, prompt)
            
            # Parse scores
            scores = self._parse_relevance_scores(response)
            
            # Apply scores to results
            for i, result in enumerate(results):
                if i + 1 in scores:
                    result.relevance_score = scores[i + 1]
                else:
                    result.relevance_score = 0.5  # Default score
            
            # Sort by relevance
            results.sort(key=lambda r: r.relevance_score or 0, reverse=True)
            
        except Exception as e:
            logger.error(f"Error scoring relevance: {e}")
            # Default all scores to 0.5 on error
            for result in results:
                result.relevance_score = 0.5
        
        return results
    
    def _parse_relevance_scores(self, response: str) -> Dict[int, float]:
        """Parse relevance scores from LLM response."""
        scores = {}
        
        # Look for patterns like "1:0.9" or "1: 0.9"
        import re
        pattern = r'(\d+)\s*:\s*(0?\.\d+|1\.0|0|1)'
        matches = re.findall(pattern, response)
        
        for position, score in matches:
            try:
                scores[int(position)] = float(score)
            except ValueError:
                continue
        
        return scores
    
    async def _take_screenshot(self, page: Page, filename: str):
        """Take a screenshot for debugging."""
        try:
            await page.screenshot(path=f"debug_{filename}")
            logger.info(f"Screenshot saved: debug_{filename}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
    
    async def search_with_pagination(
        self,
        query: str,
        total_results: int = 30,
        results_per_page: int = 10
    ) -> List[SearchResult]:
        """
        Search with pagination support.
        
        Args:
            query: Search query
            total_results: Total results to fetch
            results_per_page: Results per page (typically 10 for Google)
            
        Returns:
            Combined list of results from all pages
        """
        all_results = []
        page_num = 0
        
        while len(all_results) < total_results:
            # Calculate offset
            start = page_num * results_per_page
            
            # Modify query for pagination
            paginated_query = f"{query}&start={start}" if page_num > 0 else query
            
            # Get results for this page
            page_results = await self.search(
                paginated_query, 
                max_results=min(results_per_page, total_results - len(all_results)),
                score_relevance=False  # Score all at once at the end
            )
            
            if not page_results:
                # No more results
                break
            
            all_results.extend(page_results)
            page_num += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Score all results together
        if all_results:
            all_results = await self._score_relevance(query, all_results)
        
        return all_results[:total_results]


# Convenience functions for synchronous usage
def search_sync(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for web search.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        
    Returns:
        List of result dictionaries
    """
    async def _search():
        async with WebSearcher() as searcher:
            results = await searcher.search(query, max_results)
            return [r.to_dict() for r in results]
    
    return asyncio.run(_search())


def search_with_pagination_sync(query: str, total_results: int = 30) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for paginated search.
    
    Args:
        query: Search query
        total_results: Total results to fetch
        
    Returns:
        List of result dictionaries
    """
    async def _search():
        async with WebSearcher() as searcher:
            results = await searcher.search_with_pagination(query, total_results)
            return [r.to_dict() for r in results]
    
    return asyncio.run(_search())