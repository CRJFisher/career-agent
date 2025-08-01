"""
Tests for web scraper utility.

Tests web scraping functionality including:
- HTML content extraction
- PDF content extraction
- Error handling
- Content cleaning
- Metadata extraction
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup

from utils.web_scraper import WebScraper, scrape_url, scrape_multiple_urls


class TestWebScraper:
    """Test WebScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create WebScraper instance."""
        return WebScraper(timeout=10, max_retries=2)
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML content."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <meta property="og:title" content="OG Test Title">
        </head>
        <body>
            <nav>Navigation content to remove</nav>
            <header>Header to remove</header>
            
            <main>
                <article>
                    <h1>Main Article Title</h1>
                    <p>This is the main content of the article.</p>
                    <p>It contains multiple paragraphs with useful information.</p>
                    <div class="content">
                        <p>More content inside a div.</p>
                    </div>
                </article>
            </main>
            
            <aside class="sidebar">Sidebar to remove</aside>
            <footer>Footer to remove</footer>
            
            <script>console.log('Script to remove');</script>
        </body>
        </html>
        """
    
    @pytest.fixture
    def mock_response(self, sample_html):
        """Create mock response object."""
        response = Mock()
        response.text = sample_html
        response.content = sample_html.encode('utf-8')
        response.headers = {'Content-Type': 'text/html; charset=utf-8'}
        response.raise_for_status = Mock()
        return response
    
    def test_initialization(self):
        """Test WebScraper initialization."""
        scraper = WebScraper(timeout=20, max_retries=5)
        assert scraper.timeout == 20
        assert scraper.session is not None
    
    def test_scrape_url_success(self, scraper, mock_response):
        """Test successful URL scraping."""
        with patch.object(scraper, '_fetch_url', return_value=mock_response):
            content = scraper.scrape_url("https://example.com")
            
            assert content is not None
            assert "Main Article Title" in content
            assert "main content of the article" in content
            assert "Navigation content" not in content
            assert "Footer to remove" not in content
            assert "console.log" not in content
    
    def test_scrape_url_invalid_url(self, scraper):
        """Test scraping with invalid URL."""
        content = scraper.scrape_url("not-a-valid-url")
        assert content is None
    
    def test_scrape_url_fetch_failure(self, scraper):
        """Test scraping when fetch fails."""
        with patch.object(scraper, '_fetch_url', return_value=None):
            content = scraper.scrape_url("https://example.com")
            assert content is None
    
    def test_fetch_url_success(self, scraper, mock_response):
        """Test successful URL fetching."""
        with patch.object(scraper.session, 'get', return_value=mock_response):
            response = scraper._fetch_url("https://example.com")
            
            assert response is not None
            assert response == mock_response
            scraper.session.get.assert_called_once()
    
    def test_fetch_url_timeout(self, scraper):
        """Test URL fetch timeout."""
        with patch.object(scraper.session, 'get', side_effect=requests.exceptions.Timeout()):
            response = scraper._fetch_url("https://example.com")
            assert response is None
    
    def test_fetch_url_request_exception(self, scraper):
        """Test URL fetch with request exception."""
        with patch.object(scraper.session, 'get', side_effect=requests.exceptions.ConnectionError()):
            response = scraper._fetch_url("https://example.com")
            assert response is None
    
    def test_extract_html_content(self, scraper, sample_html):
        """Test HTML content extraction."""
        content = scraper._extract_html_content(sample_html, "https://example.com")
        
        assert "Main Article Title" in content
        assert "main content of the article" in content
        assert "More content inside a div" in content
        assert "Navigation content" not in content
        assert "Sidebar to remove" not in content
    
    def test_find_main_content_with_article(self, scraper):
        """Test finding main content with article tag."""
        html = """
        <body>
            <nav>Nav</nav>
            <article>
                <h1>Article Title</h1>
                <p>Article content goes here.</p>
            </article>
            <footer>Footer</footer>
        </body>
        """
        soup = BeautifulSoup(html, 'html.parser')
        main_content = scraper._find_main_content(soup)
        
        assert main_content is not None
        assert main_content.name == 'article'
    
    def test_find_main_content_by_class(self, scraper):
        """Test finding main content by class name."""
        html = """
        <body>
            <div class="content-wrapper">
                <h1>Content Title</h1>
                <p>This is the main content area with lots of text that should be detected.</p>
                <p>More content to ensure it's long enough.</p>
                <p>And even more content to make it the largest block.</p>
            </div>
            <div class="sidebar">Short sidebar</div>
        </body>
        """
        soup = BeautifulSoup(html, 'html.parser')
        main_content = scraper._find_main_content(soup)
        
        assert main_content is not None
        assert 'content' in main_content.get('class', [])[0]
    
    def test_find_main_content_by_size(self, scraper):
        """Test finding main content by text size."""
        html = """
        <body>
            <div class="small">Short text</div>
            <div class="large">
                This is a much larger block of text that should be identified as the main content
                because it has significantly more text than the other elements on the page.
                We need enough text here to exceed the 200 character threshold.
                Adding more content to ensure this is selected.
            </div>
            <div class="medium">Medium amount of text here</div>
        </body>
        """
        soup = BeautifulSoup(html, 'html.parser')
        main_content = scraper._find_main_content(soup)
        
        assert main_content is not None
        assert 'large' in main_content.get('class', [])
    
    def test_clean_text(self, scraper):
        """Test text cleaning function."""
        dirty_text = """
        
        Too much     whitespace    here
        
        
        And multiple


        newlines
        
        Short
        This line is long enough to keep
        X
        Another good line with content
        
        """
        
        cleaned = scraper._clean_text(dirty_text)
        
        assert "Too much whitespace here" in cleaned
        assert "And multiple" in cleaned
        assert "newlines" in cleaned
        # Text cleaning removes short lines
        lines = cleaned.split('\n')
        long_lines = [l for l in lines if len(l.strip()) > 10]
        assert "This line is long enough to keep" in cleaned
        assert "Another good line with content" in cleaned
    
    def test_extract_pdf_content_no_pypdf(self, scraper):
        """Test PDF extraction when pypdf is not available."""
        with patch.dict('sys.modules', {'pypdf': None}):
            content = scraper._extract_pdf_content(b"fake pdf content")
            assert content is None
    
    @patch('pypdf.PdfReader')
    def test_extract_pdf_content_success(self, mock_pdf_reader, scraper):
        """Test successful PDF content extraction."""
        # Mock PDF reader
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF page content"
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        content = scraper._extract_pdf_content(b"fake pdf content")
        
        assert content is not None
        assert "PDF page content" in content
    
    def test_scrape_url_pdf_content(self, scraper):
        """Test scraping PDF URL."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.content = b"fake pdf content"
        
        with patch.object(scraper, '_fetch_url', return_value=mock_response):
            with patch.object(scraper, '_extract_pdf_content', return_value="PDF text"):
                content = scraper.scrape_url("https://example.com/doc.pdf")
                
                assert content == "PDF text"
    
    def test_scrape_url_unsupported_content_type(self, scraper):
        """Test scraping unsupported content type."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'image/jpeg'}
        
        with patch.object(scraper, '_fetch_url', return_value=mock_response):
            content = scraper.scrape_url("https://example.com/image.jpg")
            assert content is None
    
    def test_scrape_multiple(self, scraper):
        """Test scraping multiple URLs."""
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        with patch.object(scraper, 'scrape_url') as mock_scrape:
            mock_scrape.side_effect = ["Content 1", None, "Content 3"]
            
            results = scraper.scrape_multiple(urls)
            
            assert len(results) == 3
            assert results["https://example1.com"] == "Content 1"
            assert results["https://example2.com"] is None
            assert results["https://example3.com"] == "Content 3"
    
    def test_extract_metadata(self, scraper, mock_response):
        """Test metadata extraction."""
        with patch.object(scraper, '_fetch_url', return_value=mock_response):
            metadata = scraper.extract_metadata("https://example.com")
            
            assert metadata is not None
            assert metadata['title'] == "Test Page"
            assert metadata['description'] == "Test description"
            assert metadata['og_title'] == "OG Test Title"
    
    def test_extract_metadata_failure(self, scraper):
        """Test metadata extraction failure."""
        with patch.object(scraper, '_fetch_url', return_value=None):
            metadata = scraper.extract_metadata("https://example.com")
            assert metadata is None


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('utils.web_scraper.WebScraper')
    def test_scrape_url_function(self, mock_scraper_class):
        """Test scrape_url convenience function."""
        mock_instance = Mock()
        mock_instance.scrape_url.return_value = "Test content"
        mock_scraper_class.return_value = mock_instance
        
        content = scrape_url("https://example.com", timeout=20)
        
        mock_scraper_class.assert_called_once_with(timeout=20)
        mock_instance.scrape_url.assert_called_once_with("https://example.com")
        assert content == "Test content"
    
    @patch('utils.web_scraper.WebScraper')
    def test_scrape_multiple_urls_function(self, mock_scraper_class):
        """Test scrape_multiple_urls convenience function."""
        mock_instance = Mock()
        mock_instance.scrape_multiple.return_value = {"url1": "content1"}
        mock_scraper_class.return_value = mock_instance
        
        urls = ["https://example1.com", "https://example2.com"]
        results = scrape_multiple_urls(urls, timeout=15)
        
        mock_scraper_class.assert_called_once_with(timeout=15)
        mock_instance.scrape_multiple.assert_called_once_with(urls)
        assert results == {"url1": "content1"}


class TestIntegration:
    """Integration tests (require internet connection)."""
    
    @pytest.mark.integration
    @pytest.mark.skipif(True, reason="Skip integration tests by default")
    def test_real_website_scraping(self):
        """Test scraping a real website."""
        scraper = WebScraper()
        content = scraper.scrape_url("https://example.com")
        
        assert content is not None
        assert "Example Domain" in content
        assert len(content) > 100