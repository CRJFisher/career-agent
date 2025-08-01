"""
Tests for web search utility.

Tests browser-based search functionality including:
- Browser initialization and cleanup
- Search result extraction
- Relevance scoring
- Pagination support
- Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from utils.web_search import WebSearcher, SearchResult, search_sync


class TestSearchResult:
    """Test SearchResult class."""
    
    def test_search_result_initialization(self):
        """Test SearchResult creation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            position=1
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.position == 1
        assert result.relevance_score is None
    
    def test_search_result_to_dict(self):
        """Test converting SearchResult to dictionary."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            position=1
        )
        result.relevance_score = 0.9
        
        result_dict = result.to_dict()
        
        assert result_dict == {
            "title": "Test Title",
            "url": "https://example.com",
            "snippet": "Test snippet",
            "position": 1,
            "relevance_score": 0.9
        }


class TestWebSearcher:
    """Test WebSearcher class."""
    
    @pytest.fixture
    def mock_browser(self):
        """Create mock browser."""
        mock = AsyncMock()
        mock.new_page = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_page(self):
        """Create mock page."""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.content = AsyncMock()
        page.close = AsyncMock()
        page.screenshot = AsyncMock()
        return page
    
    @pytest.fixture
    def sample_html(self):
        """Sample Google search results HTML."""
        return """
        <div id="search">
            <div class="g">
                <a href="https://example1.com">
                    <h3>Example 1 Title</h3>
                </a>
                <div data-sncf="1">This is the first example snippet</div>
            </div>
            <div class="g">
                <a href="https://example2.com">
                    <h3>Example 2 Title</h3>
                </a>
                <span class="aCOpRe">This is the second example snippet</span>
            </div>
            <div class="g">
                <div>Sponsored</div>
                <a href="https://ad.com">
                    <h3>Ad Title</h3>
                </a>
            </div>
        </div>
        """
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        with patch('utils.web_search.async_playwright') as mock_playwright:
            with patch('utils.web_search.get_default_llm_wrapper'):
                mock_pw_instance = AsyncMock()
                mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
                mock_browser = AsyncMock()
                mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
                
                async with WebSearcher() as searcher:
                    assert searcher.browser is not None
                    mock_pw_instance.chromium.launch.assert_called_once()
                
                mock_browser.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_basic(self, mock_browser, mock_page, sample_html):
        """Test basic search functionality."""
        with patch('utils.web_search.get_default_llm_wrapper'):
            searcher = WebSearcher()
            searcher.browser = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.content.return_value = sample_html
            
            results = await searcher.search("test query", max_results=5, score_relevance=False)
            
            assert len(results) == 2  # Should exclude the ad
            assert results[0].title == "Example 1 Title"
            assert results[0].url == "https://example1.com"
            assert results[0].snippet == "This is the first example snippet"
            assert results[1].title == "Example 2 Title"
    
    @pytest.mark.asyncio
    async def test_search_with_relevance_scoring(self, mock_browser, mock_page, sample_html):
        """Test search with relevance scoring."""
        with patch('utils.web_search.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_llm_sync = Mock(return_value="1:0.9, 2:0.7")
            mock_get_llm.return_value = mock_llm
            
            searcher = WebSearcher()
            searcher.browser = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.content.return_value = sample_html
            
            results = await searcher.search("test query", score_relevance=True)
            
            assert len(results) == 2
            assert results[0].relevance_score == 0.9
            assert results[1].relevance_score == 0.7
            mock_llm.call_llm_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_timeout_handling(self, mock_browser, mock_page):
        """Test handling of page timeout."""
        with patch('utils.web_search.get_default_llm_wrapper'):
            from playwright.async_api import TimeoutError as PlaywrightTimeout
            
            searcher = WebSearcher()
            searcher.browser = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.wait_for_selector.side_effect = PlaywrightTimeout("Timeout")
            
            results = await searcher.search("test query")
            
            assert results == []
            mock_page.screenshot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, mock_browser, mock_page):
        """Test general error handling."""
        with patch('utils.web_search.get_default_llm_wrapper'):
            searcher = WebSearcher()
            searcher.browser = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.goto.side_effect = Exception("Network error")
            
            results = await searcher.search("test query")
            
            assert results == []
            mock_page.close.assert_called_once()
    
    def test_is_ad(self):
        """Test ad detection."""
        from bs4 import BeautifulSoup
        
        with patch('utils.web_search.get_default_llm_wrapper'):
            searcher = WebSearcher()
        
            # Test sponsored content
            ad_html = '<div class="g">Sponsored content</div>'
            ad_soup = BeautifulSoup(ad_html, 'html.parser').div
            assert searcher._is_ad(ad_soup) is True
            
            # Test regular content
            regular_html = '<div class="g">Regular content</div>'
            regular_soup = BeautifulSoup(regular_html, 'html.parser').div
            assert searcher._is_ad(regular_soup) is False
    
    def test_parse_relevance_scores(self):
        """Test parsing relevance scores from LLM response."""
        with patch('utils.web_search.get_default_llm_wrapper'):
            searcher = WebSearcher()
        
            # Test various formats
            response = """
            1: 0.9
            2:0.7
            3 : 0.5
            4: 1.0
            """
            
            scores = searcher._parse_relevance_scores(response)
            
            assert scores[1] == 0.9
            assert scores[2] == 0.7
            assert scores[3] == 0.5
            assert scores[4] == 1.0
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(self, mock_browser, mock_page, sample_html):
        """Test paginated search."""
        with patch('utils.web_search.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_llm.call_llm_sync = Mock(return_value="1:0.9, 2:0.8")
            mock_get_llm.return_value = mock_llm
            
            searcher = WebSearcher()
            searcher.browser = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.content.return_value = sample_html
            
            # Mock search method to return different results for each page
            original_search = searcher.search
            call_count = 0
            
            async def mock_search(query, max_results=10, score_relevance=True):
                nonlocal call_count
                call_count += 1
                if call_count > 2:  # Stop after 2 pages
                    return []
                return await original_search(query, max_results, score_relevance)
            
            searcher.search = mock_search
            
            results = await searcher.search_with_pagination("test query", total_results=5)
            
            assert len(results) <= 5
            assert call_count >= 2  # Should have tried multiple pages
    
    @pytest.mark.asyncio
    async def test_browser_not_started_error(self):
        """Test error when browser not started."""
        with patch('utils.web_search.get_default_llm_wrapper'):
            searcher = WebSearcher()
        
            with pytest.raises(RuntimeError, match="Browser not started"):
                await searcher.search("test query")


class TestSyncWrappers:
    """Test synchronous wrapper functions."""
    
    @patch('utils.web_search.WebSearcher')
    def test_search_sync(self, mock_searcher_class):
        """Test synchronous search wrapper."""
        # Create mock searcher instance
        mock_searcher = AsyncMock()
        mock_searcher_class.return_value = mock_searcher
        
        # Mock search results
        mock_results = [
            SearchResult("Title 1", "http://url1.com", "Snippet 1", 1),
            SearchResult("Title 2", "http://url2.com", "Snippet 2", 2)
        ]
        mock_searcher.search.return_value = mock_results
        
        # Mock context manager
        mock_searcher.__aenter__.return_value = mock_searcher
        mock_searcher.__aexit__.return_value = None
        
        # Call sync function
        with patch('asyncio.run') as mock_run:
            # Make asyncio.run execute the coroutine
            async def run_coro(coro):
                return await coro
            
            mock_run.side_effect = lambda coro: asyncio.get_event_loop().run_until_complete(run_coro(coro))
            
            # Create new event loop for test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = search_sync("test query", max_results=5)
                
                # Verify results
                assert len(results) == 2
                assert results[0]["title"] == "Title 1"
                assert results[1]["url"] == "http://url2.com"
            finally:
                loop.close()


class TestIntegration:
    """Integration tests (skipped if Playwright not installed)."""
    
    @pytest.mark.skipif(
        not pytest.importorskip("playwright", reason="Playwright not installed"),
        reason="Playwright required for integration tests"
    )
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_browser_search(self):
        """Test with real browser (requires Playwright installed)."""
        async with WebSearcher(headless=True) as searcher:
            results = await searcher.search("Python programming", max_results=3)
            
            assert len(results) > 0
            assert all(r.title for r in results)
            assert all(r.url.startswith("http") for r in results)