"""Tests for BrowserActionNode.

This module tests the AI-powered browser functionality for job applications.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from nodes import BrowserActionNode


class TestBrowserActionNode:
    """Test suite for BrowserActionNode."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM wrapper."""
        mock = Mock()
        mock.call_llm_sync = Mock(return_value="")
        mock.call_llm = AsyncMock(return_value="")
        return mock
    
    @pytest.fixture
    def node(self, mock_llm):
        """Create a BrowserActionNode instance with mocked dependencies."""
        with patch('nodes.get_default_llm_wrapper', return_value=mock_llm):
            with patch('nodes.AI_BROWSER_AVAILABLE', True):
                return BrowserActionNode()
    
    @pytest.fixture
    def shared_store(self):
        """Create a shared store with browser action config."""
        return {
            "browser_action": {
                "action_type": "extract_jobs",
                "url": "https://example.com/jobs"
            }
        }
    
    def test_prep_valid_config(self, node, shared_store):
        """Test prep with valid browser action config."""
        result = node.prep(shared_store)
        
        assert result == shared_store["browser_action"]
        assert "action_type" in result
        assert result["action_type"] == "extract_jobs"
    
    def test_prep_missing_config(self, node):
        """Test prep with missing browser action config."""
        shared = {}
        
        with pytest.raises(ValueError, match="No browser action configuration found"):
            node.prep(shared)
    
    def test_prep_missing_action_type(self, node):
        """Test prep with missing action_type."""
        shared = {"browser_action": {"url": "https://example.com"}}
        
        with pytest.raises(ValueError, match="browser_action must specify action_type"):
            node.prep(shared)
    
    @pytest.mark.asyncio
    async def test_exec_extract_jobs(self, node, mock_llm):
        """Test exec with extract_jobs action."""
        action_config = {
            "action_type": "extract_jobs",
            "url": "https://example.com/jobs"
        }
        
        # Mock the browser
        mock_browser = AsyncMock()
        mock_browser.navigate_and_extract = AsyncMock(return_value={
            "data": [
                {"title": "Software Engineer", "company": "TechCo", "location": "Remote"},
                {"title": "Data Scientist", "company": "DataCo", "location": "NYC"}
            ]
        })
        
        with patch.object(node, '_setup_browser', AsyncMock()):
            node.browser = mock_browser
            
            result = await node._exec_async(action_config)
        
        assert result["success"] is True
        assert len(result["job_listings"]) == 2
        assert result["job_listings"][0]["title"] == "Software Engineer"
        assert result["url"] == "https://example.com/jobs"
    
    @pytest.mark.asyncio
    async def test_exec_fill_application(self, node, mock_llm):
        """Test exec with fill_application action."""
        action_config = {
            "action_type": "fill_application",
            "url": "https://example.com/apply",
            "form_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "resume": "path/to/resume.pdf"
            },
            "submit": False
        }
        
        # Mock the browser
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        mock_browser.page = mock_page
        mock_browser._fill_job_form = AsyncMock(return_value="Successfully filled 3 fields: name, email, resume")
        
        with patch.object(node, '_setup_browser', AsyncMock()):
            node.browser = mock_browser
            
            result = await node._exec_async(action_config)
        
        assert result["success"] is True
        assert "Successfully filled 3 fields" in result["status"]
        assert result["url"] == "https://example.com/apply"
    
    @pytest.mark.asyncio
    async def test_exec_navigate_and_extract(self, node, mock_llm):
        """Test exec with navigate_and_extract action."""
        action_config = {
            "action_type": "navigate_and_extract",
            "url": "https://example.com/about",
            "instruction": "Extract company values and culture information"
        }
        
        # Mock the browser
        mock_browser = AsyncMock()
        mock_browser.navigate_and_extract = AsyncMock(return_value={
            "values": ["Innovation", "Collaboration", "Excellence"],
            "culture": "Fast-paced startup environment"
        })
        
        with patch.object(node, '_setup_browser', AsyncMock()):
            node.browser = mock_browser
            
            result = await node._exec_async(action_config)
        
        assert result["success"] is True
        assert "values" in result["extracted_data"]
        assert len(result["extracted_data"]["values"]) == 3
        assert result["url"] == "https://example.com/about"
    
    @pytest.mark.asyncio
    async def test_exec_simple_extract(self, node, mock_llm):
        """Test exec with simple_extract action."""
        action_config = {
            "action_type": "simple_extract",
            "url": "https://example.com/team",
            "prompt": "Extract team size and department structure"
        }
        
        # Mock the AISimpleScraper
        with patch('nodes.AISimpleScraper') as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper.extract = AsyncMock(return_value={
                "team_size": 150,
                "departments": ["Engineering", "Product", "Sales", "Marketing"]
            })
            mock_scraper_class.return_value = mock_scraper
            
            with patch.object(node, '_setup_browser', AsyncMock()):
                result = await node._exec_async(action_config)
        
        assert result["success"] is True
        assert result["extracted_data"]["team_size"] == 150
        assert len(result["extracted_data"]["departments"]) == 4
    
    @pytest.mark.asyncio
    async def test_exec_unknown_action(self, node, mock_llm):
        """Test exec with unknown action type."""
        action_config = {
            "action_type": "unknown_action",
            "url": "https://example.com"
        }
        
        with patch.object(node, '_setup_browser', AsyncMock()):
            result = await node._exec_async(action_config)
        
        assert result["success"] is False
        assert "Unknown action type: unknown_action" in result["error"]
        assert result["action_type"] == "unknown_action"
    
    @pytest.mark.asyncio
    async def test_exec_error_handling(self, node, mock_llm):
        """Test exec error handling."""
        action_config = {
            "action_type": "extract_jobs",
            "url": "https://example.com/jobs"
        }
        
        # Mock browser to raise an error
        with patch.object(node, '_setup_browser', AsyncMock(side_effect=Exception("Browser failed to start"))):
            result = await node._exec_async(action_config)
        
        assert result["success"] is False
        assert "Browser failed to start" in result["error"]
        assert result["action_type"] == "extract_jobs"
    
    def test_post_success_extract_jobs(self, node, shared_store):
        """Test post with successful job extraction."""
        action_config = {"action_type": "extract_jobs"}
        exec_res = {
            "success": True,
            "job_listings": [
                {"title": "Software Engineer", "company": "TechCo"}
            ]
        }
        
        result = node.post(shared_store, action_config, exec_res)
        
        assert result == "browser_success"
        assert "browser_action_result" in shared_store
        assert "extracted_job_listings" in shared_store
        assert len(shared_store["extracted_job_listings"]) == 1
    
    def test_post_success_fill_application(self, node, shared_store):
        """Test post with successful form filling."""
        action_config = {"action_type": "fill_application"}
        exec_res = {
            "success": True,
            "status": "Form filled successfully"
        }
        
        result = node.post(shared_store, action_config, exec_res)
        
        assert result == "browser_success"
        assert "application_status" in shared_store
        assert shared_store["application_status"] == "Form filled successfully"
    
    def test_post_failure(self, node, shared_store):
        """Test post with failed action."""
        action_config = {"action_type": "extract_jobs"}
        exec_res = {
            "success": False,
            "error": "Failed to load page"
        }
        
        result = node.post(shared_store, action_config, exec_res)
        
        assert result == "browser_failed"
        assert "browser_action_result" in shared_store
        assert "extracted_job_listings" not in shared_store
    
    def test_browser_not_available(self, mock_llm):
        """Test node creation when browser dependencies are not available."""
        with patch('nodes.AI_BROWSER_AVAILABLE', False):
            with pytest.raises(ImportError, match="BrowserActionNode requires AI browser dependencies"):
                BrowserActionNode()
    
    @pytest.mark.asyncio
    async def test_browser_cleanup(self, node, mock_llm):
        """Test browser cleanup on node destruction."""
        # Setup mock browser
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        node.browser = mock_browser
        
        # Call cleanup
        await node._cleanup_browser()
        
        mock_browser.close.assert_called_once()
        assert node.browser is None