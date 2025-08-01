"""
Tests for research agent tool nodes.

Tests the tool execution nodes including:
- WebSearchNode
- ReadContentNode  
- SynthesizeInfoNode
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from typing import List, Dict, Any

from nodes import WebSearchNode, ReadContentNode, SynthesizeInfoNode


class TestWebSearchNode:
    """Test suite for WebSearchNode."""
    
    @pytest.fixture
    def node(self):
        """Create WebSearchNode instance."""
        return WebSearchNode()
    
    @pytest.fixture
    def sample_shared_store(self):
        """Sample shared store with search action."""
        return {
            "action_params": {
                "query": "TechCorp company culture",
                "max_results": 5
            }
        }
    
    @pytest.fixture
    def sample_search_results(self):
        """Sample search results."""
        return [
            {
                "title": "TechCorp - About Us",
                "url": "https://techcorp.com/about",
                "snippet": "Learn about TechCorp's innovative culture..."
            },
            {
                "title": "Working at TechCorp - Reviews",
                "url": "https://reviews.com/techcorp",
                "snippet": "Employee reviews of TechCorp culture..."
            }
        ]
    
    def test_prep_success(self, node, sample_shared_store):
        """Test successful prep with valid query."""
        result = node.prep(sample_shared_store)
        
        assert result["query"] == "TechCorp company culture"
        assert result["max_results"] == 5
    
    def test_prep_no_query(self, node):
        """Test prep with missing query."""
        shared = {"action_params": {}}
        
        with pytest.raises(ValueError, match="No search query provided"):
            node.prep(shared)
    
    def test_prep_default_max_results(self, node):
        """Test prep with default max_results."""
        shared = {
            "action_params": {"query": "test query"}
        }
        
        result = node.prep(shared)
        assert result["max_results"] == 10
    
    @patch('asyncio.set_event_loop')
    @patch('asyncio.new_event_loop')  
    @patch('utils.web_search.WebSearcher')
    def test_exec_success(self, mock_searcher_class, mock_new_loop, mock_set_loop, node, sample_search_results):
        """Test successful search execution."""
        # Create mock search results with to_dict method
        mock_results = []
        for res in sample_search_results:
            mock_res = Mock()
            mock_res.to_dict.return_value = res
            mock_results.append(mock_res)
        
        # Create a mock event loop
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        
        # Create async context manager mock
        mock_searcher = AsyncMock()
        mock_searcher.search.return_value = mock_results
        mock_searcher_class.return_value.__aenter__.return_value = mock_searcher
        mock_searcher_class.return_value.__aexit__.return_value = None
        
        # Make run_until_complete return the expected results
        mock_loop.run_until_complete.return_value = sample_search_results
        
        result = node.exec({"query": "TechCorp", "max_results": 5})
        
        assert result == sample_search_results
        mock_loop.close.assert_called_once()
    
    @patch('utils.web_search.WebSearcher')
    def test_exec_failure(self, mock_searcher_class, node):
        """Test search execution failure."""
        # Make searcher raise exception
        mock_searcher_class.side_effect = Exception("Search failed")
        
        with patch('asyncio.new_event_loop'):
            result = node.exec({"query": "test", "max_results": 5})
            
            assert result == []
    
    def test_post_updates_shared(self, node, sample_shared_store, sample_search_results):
        """Test post updates shared store correctly."""
        result = node.post(sample_shared_store, {}, sample_search_results)
        
        assert result == "decide"
        assert sample_shared_store["search_results"] == sample_search_results
        assert "research_state" in sample_shared_store
        assert len(sample_shared_store["research_state"]["information_gathered"]["search_results"]) == 2
    
    def test_post_appends_to_existing(self, node, sample_search_results):
        """Test post appends to existing search results."""
        shared = {
            "research_state": {
                "information_gathered": {
                    "search_results": [{"title": "Existing result"}]
                }
            }
        }
        
        node.post(shared, {}, sample_search_results)
        
        assert len(shared["research_state"]["information_gathered"]["search_results"]) == 3


class TestReadContentNode:
    """Test suite for ReadContentNode."""
    
    @pytest.fixture
    def node(self):
        """Create ReadContentNode instance."""
        return ReadContentNode()
    
    @pytest.fixture 
    def sample_shared_store(self):
        """Sample shared store with read action."""
        return {
            "action_params": {
                "url": "https://techcorp.com/about",
                "focus": "company values"
            }
        }
    
    def test_prep_success(self, node, sample_shared_store):
        """Test successful prep with valid URL."""
        result = node.prep(sample_shared_store)
        
        assert result["url"] == "https://techcorp.com/about"
        assert result["focus"] == "company values"
    
    def test_prep_no_url(self, node):
        """Test prep with missing URL."""
        shared = {"action_params": {}}
        
        with pytest.raises(ValueError, match="No URL provided to read"):
            node.prep(shared)
    
    def test_prep_no_focus(self, node):
        """Test prep without focus parameter."""
        shared = {
            "action_params": {"url": "https://example.com"}
        }
        
        result = node.prep(shared)
        assert result["url"] == "https://example.com"
        assert result["focus"] == ""
    
    @patch('utils.web_scraper.scrape_url')
    def test_exec_success(self, mock_scrape, node):
        """Test successful content extraction."""
        mock_scrape.return_value = "Page content about company values..."
        
        result = node.exec({"url": "https://example.com", "focus": "values"})
        
        assert result == "Page content about company values..."
        mock_scrape.assert_called_once_with("https://example.com")
    
    @patch('utils.web_scraper.scrape_url')
    def test_exec_failure(self, mock_scrape, node):
        """Test content extraction failure."""
        mock_scrape.side_effect = Exception("Scraping failed")
        
        result = node.exec({"url": "https://example.com", "focus": ""})
        
        assert result is None
    
    def test_post_success(self, node, sample_shared_store):
        """Test post with successful content extraction."""
        content = "Company values content..."
        prep_res = {"url": "https://techcorp.com/about", "focus": "values"}
        
        result = node.post(sample_shared_store, prep_res, content)
        
        assert result == "decide"
        assert sample_shared_store["current_content"] == content
        assert sample_shared_store["current_url"] == "https://techcorp.com/about"
        assert "research_state" in sample_shared_store
        
        content_info = sample_shared_store["research_state"]["information_gathered"]["content_to_analyze"]
        assert len(content_info) == 1
        assert content_info[0]["url"] == "https://techcorp.com/about"
        assert content_info[0]["has_content"] is True
    
    def test_post_failure(self, node, sample_shared_store):
        """Test post with failed content extraction."""
        prep_res = {"url": "https://fail.com", "focus": ""}
        
        result = node.post(sample_shared_store, prep_res, None)
        
        assert result == "decide"
        assert sample_shared_store["current_content"] is None
        assert sample_shared_store["current_url"] == "https://fail.com"


class TestSynthesizeInfoNode:
    """Test suite for SynthesizeInfoNode."""
    
    @pytest.fixture
    def node(self):
        """Create SynthesizeInfoNode instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return SynthesizeInfoNode()
    
    @pytest.fixture
    def sample_shared_store(self):
        """Sample shared store with research data."""
        return {
            "company_name": "TechCorp",
            "job_title": "Senior Engineer",
            "research_goals": ["Company culture", "Tech stack"],
            "research_state": {
                "information_gathered": {
                    "search_results": [
                        {
                            "title": "TechCorp Culture",
                            "snippet": "TechCorp values innovation..."
                        }
                    ]
                }
            },
            "current_content": "TechCorp is a leading technology company focused on AI..."
        }
    
    def test_prep_success(self, node, sample_shared_store):
        """Test successful prep with research data."""
        result = node.prep(sample_shared_store)
        
        assert "Search Result: TechCorp Culture" in result["content"]
        assert "TechCorp values innovation" in result["content"]
        assert "Page Content:" in result["content"]
        assert result["company_name"] == "TechCorp"
        assert result["job_title"] == "Senior Engineer"
        assert len(result["research_goals"]) == 2
    
    def test_prep_no_content(self, node):
        """Test prep with no content to synthesize."""
        shared = {
            "company_name": "TechCorp",
            "research_state": {"information_gathered": {}}
        }
        
        with pytest.raises(ValueError, match="No content available to synthesize"):
            node.prep(shared)
    
    def test_exec_success(self, node):
        """Test successful synthesis execution."""
        context = {
            "content": "Research content",
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": ["Culture"]
        }
        
        # Mock LLM response
        node.llm.call_llm_structured_sync.return_value = {
            "company_culture_values": ["Remote-first", "Innovation focused"],
            "technology_stack_practices": ["Python", "Kubernetes"],
            "recent_developments": ["New AI product launch"],
            "team_work_environment": ["Agile teams"],
            "market_position_growth": ["Market leader"],
            "other_notable": ["Great benefits"]
        }
        
        result = node.exec(context)
        
        assert "company_culture_values" in result
        assert len(result["company_culture_values"]) == 2
        assert result["technology_stack_practices"] == ["Python", "Kubernetes"]
    
    def test_exec_llm_failure(self, node):
        """Test synthesis with LLM failure."""
        context = {
            "content": "content",
            "company_name": "TechCorp",
            "job_title": "",
            "research_goals": []
        }
        
        node.llm.call_llm_structured_sync.side_effect = Exception("LLM error")
        
        result = node.exec(context)
        
        assert result["company_culture_values"] == ["No information synthesized"]
        assert result["other_notable"] == ["Synthesis failed"]
    
    def test_post_updates_research(self, node, sample_shared_store):
        """Test post updates company research."""
        exec_res = {
            "company_culture_values": ["Remote-first"],
            "technology_stack_practices": ["Python"],
            "recent_developments": [],
            "team_work_environment": ["Agile"],
            "market_position_growth": [],
            "other_notable": []
        }
        
        result = node.post(sample_shared_store, {}, exec_res)
        
        assert result == "decide"
        assert "company_research" in sample_shared_store
        assert sample_shared_store["company_research"]["company_culture_values"] == ["Remote-first"]
        assert sample_shared_store["research_state"]["synthesis_complete"] is True
        
        # Check categories added to information_gathered
        info = sample_shared_store["research_state"]["information_gathered"]
        assert info["company_culture_values"] == ["Remote-first"]
        assert info["technology_stack_practices"] == ["Python"]
        assert info["team_work_environment"] == ["Agile"]
    
    def test_build_prompt(self, node):
        """Test synthesis prompt construction."""
        context = {
            "content": "Test content",
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": ["Culture", "Tech"]
        }
        
        # Call exec to trigger prompt building
        node.llm.call_llm_structured_sync.return_value = {}
        node.exec(context)
        
        # Check prompt was called with expected content
        call_args = node.llm.call_llm_structured_sync.call_args
        prompt = call_args[1]["prompt"]
        
        assert "TechCorp" in prompt
        assert "Engineer" in prompt
        assert "Culture" in prompt
        assert "Tech" in prompt
        assert "Test content" in prompt
        assert "Company Culture & Values" in prompt
        assert "Technology Stack & Practices" in prompt