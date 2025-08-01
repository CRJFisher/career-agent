"""
Web scraping utility for extracting clean text from URLs.

This module provides functionality to scrape web pages and extract
readable content for company research and job description analysis.
"""

import logging
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
import io

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper for extracting clean text content from URLs."""
    
    # Common user agents to avoid blocking
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    
    # Tags that typically contain main content
    CONTENT_TAGS = ['article', 'main', 'div[role="main"]', '[class*="content"]', '[class*="article"]']
    
    # Tags to remove (navigation, ads, etc.)
    REMOVE_TAGS = ['nav', 'header', 'footer', 'aside', 'script', 'style', 'noscript', 
                   '[class*="sidebar"]', '[class*="menu"]', '[class*="navigation"]',
                   '[class*="advertisement"]', '[class*="banner"]', '[id*="comments"]']
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize web scraper.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.session = self._create_session(max_retries)
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape and extract clean text content from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Clean text content or None if failed
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.error(f"Invalid URL: {url}")
                return None
            
            # Make request
            response = self._fetch_url(url)
            if not response:
                return None
            
            # Handle different content types
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                return self._extract_html_content(response.text, url)
            elif 'application/pdf' in content_type:
                return self._extract_pdf_content(response.content)
            else:
                logger.warning(f"Unsupported content type: {content_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _fetch_url(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with proper headers and error handling."""
        try:
            headers = {
                'User-Agent': self.USER_AGENTS[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
        
        return None
    
    def _extract_html_content(self, html: str, base_url: str) -> str:
        """Extract main content from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for selector in self.REMOVE_TAGS:
            for element in soup.select(selector):
                element.decompose()
        
        # Try to find main content container
        main_content = self._find_main_content(soup)
        
        if main_content:
            text = self._extract_text_from_element(main_content)
        else:
            # Fallback: extract from body
            body = soup.find('body')
            if body:
                text = self._extract_text_from_element(body)
            else:
                text = soup.get_text()
        
        # Clean and normalize text
        return self._clean_text(text)
    
    def _find_main_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find the main content container in the page."""
        # Try content selectors
        for selector in self.CONTENT_TAGS:
            content = soup.select_one(selector)
            if content:
                return content
        
        # Try heuristics - find largest text block
        candidates = []
        
        for tag in soup.find_all(['div', 'section', 'article']):
            text_length = len(tag.get_text(strip=True))
            if text_length > 200:  # Minimum content threshold
                candidates.append((tag, text_length))
        
        if candidates:
            # Return the largest content block
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]
        
        return None
    
    def _extract_text_from_element(self, element: Tag) -> str:
        """Extract text from an element, preserving some structure."""
        texts = []
        
        for elem in element.descendants:
            if isinstance(elem, NavigableString):
                parent = elem.parent
                if parent.name not in ['script', 'style']:
                    text = str(elem).strip()
                    if text:
                        texts.append(text)
            elif isinstance(elem, Tag):
                # Add spacing for block elements
                if elem.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br']:
                    texts.append('\n')
        
        return ' '.join(texts)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove very short lines (likely navigation items)
        lines = text.split('\n')
        cleaned_lines = [line for line in lines if len(line.strip()) > 10]
        
        return '\n'.join(cleaned_lines)
    
    def _extract_pdf_content(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from PDF content."""
        try:
            # Try using pypdf if available
            import pypdf
            
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            text = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text.append(page.extract_text())
            
            return self._clean_text('\n'.join(text))
            
        except ImportError:
            logger.warning("pypdf not installed. Cannot extract PDF content.")
            return None
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return None
    
    def scrape_multiple(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """
        Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            Dictionary mapping URLs to their content (or None if failed)
        """
        results = {}
        
        for url in urls:
            logger.info(f"Scraping {url}")
            content = self.scrape_url(url)
            results[url] = content
        
        return results
    
    def extract_metadata(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract metadata from a webpage.
        
        Args:
            url: URL to extract metadata from
            
        Returns:
            Dictionary with title, description, and other metadata
        """
        try:
            response = self._fetch_url(url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            metadata = {}
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)
            
            # Extract meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content', '')
            
            # Extract Open Graph data
            og_tags = soup.find_all('meta', attrs={'property': re.compile('^og:')})
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                metadata[f'og_{property_name}'] = tag.get('content', '')
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {e}")
            return None


# Convenience functions
def scrape_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        Clean text content or None if failed
    """
    scraper = WebScraper(timeout=timeout)
    return scraper.scrape_url(url)


def scrape_multiple_urls(urls: List[str], timeout: int = 30) -> Dict[str, Optional[str]]:
    """
    Convenience function to scrape multiple URLs.
    
    Args:
        urls: List of URLs to scrape
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary mapping URLs to content
    """
    scraper = WebScraper(timeout=timeout)
    return scraper.scrape_multiple(urls)