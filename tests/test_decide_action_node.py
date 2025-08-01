"""
Tests for DecideActionNode.

Tests the agent decision-making functionality including:
- Action selection based on research state
- YAML response parsing
- Research state updates
- Error handling
"""

import pytest
from unittest.mock import Mock, patch
import yaml

from nodes import DecideActionNode


class TestDecideActionNode:
    """Test suite for DecideActionNode."""
    
    @pytest.fixture
    def node(self):
        """Create a DecideActionNode instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return DecideActionNode()
    
    @pytest.fixture
    def sample_shared_store(self):
        """Sample shared store with research context."""
        return {
            "company_name": "TechCorp Inc",
            "job_title": "Senior Software Engineer",
            "research_goals": [
                "Company culture and values",
                "Technology stack",
                "Recent developments"
            ],
            "research_state": {
                "searches_performed": ["TechCorp Inc company culture"],
                "pages_read": ["https://techcorp.com/about"],
                "information_gathered": {
                    "culture": ["Remote-first company", "Focus on work-life balance"]
                },
                "synthesis_complete": False
            }
        }
    
    def test_prep_success(self, node, sample_shared_store):
        """Test successful prep with valid data."""
        result = node.prep(sample_shared_store)
        
        assert result["company_name"] == "TechCorp Inc"
        assert result["job_title"] == "Senior Software Engineer"
        assert len(result["research_goals"]) == 3
        assert "searches_performed" in result["research_state"]
    
    def test_prep_missing_company_name(self, node):
        """Test prep with missing company name."""
        shared = {
            "job_title": "Engineer",
            "research_state": {}
        }
        
        with pytest.raises(ValueError, match="No company name provided"):
            node.prep(shared)
    
    def test_prep_with_defaults(self, node):
        """Test prep with minimal data using defaults."""
        shared = {
            "company_name": "TestCo"
        }
        
        result = node.prep(shared)
        
        assert result["company_name"] == "TestCo"
        assert result["job_title"] == ""
        assert result["research_goals"] == []
        assert result["research_state"]["searches_performed"] == []
    
    def test_exec_web_search_decision(self, node):
        """Test exec returning web search action."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": ["Company culture"],
            "research_state": {
                "searches_performed": [],
                "pages_read": [],
                "information_gathered": {},
                "synthesis_complete": False
            }
        }
        
        # Mock LLM response
        llm_response = """thinking: |
  No searches performed yet. Need to start with basic company information.
  
action:
  type: web_search
  parameters:
    query: TechCorp company overview culture values"""
        
        node.llm.call_llm_sync.return_value = llm_response
        
        result = node.exec(context)
        
        assert result["action_type"] == "web_search"
        assert result["action_params"]["query"] == "TechCorp company overview culture values"
        assert "thinking" in result["decision"]
    
    def test_exec_read_content_decision(self, node):
        """Test exec returning read content action."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": ["Technology stack"],
            "research_state": {
                "searches_performed": ["TechCorp technology"],
                "pages_read": [],
                "information_gathered": {},
                "synthesis_complete": False
            }
        }
        
        # Mock LLM response
        llm_response = """thinking: |
  Found search results. Need to read the engineering blog for tech stack info.
  
action:
  type: read_content
  parameters:
    url: https://techcorp.com/engineering
    focus: technology stack and tools"""
        
        node.llm.call_llm_sync.return_value = llm_response
        
        result = node.exec(context)
        
        assert result["action_type"] == "read_content"
        assert result["action_params"]["url"] == "https://techcorp.com/engineering"
        assert result["action_params"]["focus"] == "technology stack and tools"
    
    def test_exec_synthesize_decision(self, node):
        """Test exec returning synthesize action."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": ["Company culture", "Tech stack"],
            "research_state": {
                "searches_performed": ["TechCorp culture", "TechCorp technology"],
                "pages_read": ["https://techcorp.com/about", "https://techcorp.com/careers"],
                "information_gathered": {
                    "culture": ["Remote-first", "Agile teams"],
                    "technology": ["Python", "Kubernetes", "AWS"]
                },
                "synthesis_complete": False
            }
        }
        
        # Mock LLM response
        llm_response = """thinking: |
  Have gathered information on all research goals. Time to synthesize.
  
action:
  type: synthesize
  parameters: {}"""
        
        node.llm.call_llm_sync.return_value = llm_response
        
        result = node.exec(context)
        
        assert result["action_type"] == "synthesize"
        assert result["action_params"] == {}
    
    def test_exec_finish_decision(self, node):
        """Test exec returning finish action."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": ["Company overview"],
            "research_state": {
                "searches_performed": ["TechCorp"],
                "pages_read": ["https://techcorp.com"],
                "information_gathered": {"overview": ["Leading tech company"]},
                "synthesis_complete": True
            }
        }
        
        # Mock LLM response
        llm_response = """thinking: |
  Synthesis is complete. Research is finished.
  
action:
  type: finish
  parameters: {}"""
        
        node.llm.call_llm_sync.return_value = llm_response
        
        result = node.exec(context)
        
        assert result["action_type"] == "finish"
    
    def test_exec_yaml_parse_error(self, node):
        """Test exec handling YAML parse errors."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": [],
            "research_state": {
                "searches_performed": [],
                "pages_read": [],
                "information_gathered": {},
                "synthesis_complete": False
            }
        }
        
        # Mock invalid YAML response
        node.llm.call_llm_sync.return_value = "Invalid YAML: {{"
        
        result = node.exec(context)
        
        # Should fallback to web search
        assert result["action_type"] == "web_search"
        assert result["action_params"]["query"] == "TechCorp"
        assert "Failed to parse response" in result["decision"]["thinking"]
    
    def test_exec_missing_required_fields(self, node):
        """Test exec handling missing fields in response."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Engineer",
            "research_goals": [],
            "research_state": {
                "searches_performed": [],
                "pages_read": [],
                "information_gathered": {},
                "synthesis_complete": False
            }
        }
        
        # Mock response missing action field
        node.llm.call_llm_sync.return_value = """thinking: Some thinking"""
        
        with pytest.raises(ValueError, match="Decision missing required fields"):
            node.exec(context)
    
    def test_build_agent_prompt(self, node):
        """Test agent prompt construction."""
        context = {
            "company_name": "TechCorp",
            "job_title": "Senior Engineer",
            "research_goals": ["Culture", "Tech stack"],
            "research_state": {
                "searches_performed": ["TechCorp culture"],
                "pages_read": ["https://techcorp.com"],
                "information_gathered": {
                    "culture": ["Great culture", "Remote work"]
                },
                "synthesis_complete": False
            }
        }
        
        prompt = node._build_agent_prompt(context)
        
        # Check key elements are in prompt
        assert "TechCorp" in prompt
        assert "Senior Engineer" in prompt
        assert "Culture" in prompt
        assert "Tech stack" in prompt
        assert "TechCorp culture" in prompt  # search performed
        assert "https://techcorp.com" in prompt  # page read
        assert "Great culture" in prompt  # info gathered
        assert "web_search" in prompt  # action
        assert "read_content" in prompt  # action
        assert "synthesize" in prompt  # action
        assert "finish" in prompt  # action
    
    def test_default_research_goals(self, node):
        """Test default research goals."""
        goals = node._default_research_goals()
        
        assert len(goals) > 0
        assert any("culture" in g.lower() for g in goals)
        assert any("technology" in g.lower() or "tech" in g.lower() for g in goals)
    
    def test_post_updates_state(self, node, sample_shared_store):
        """Test post updates shared store correctly."""
        prep_res = {}
        exec_res = {
            "decision": {
                "thinking": "Need more info",
                "action": {"type": "web_search", "parameters": {"query": "TechCorp news"}}
            },
            "action_type": "web_search",
            "action_params": {"query": "TechCorp news"}
        }
        
        result = node.post(sample_shared_store, prep_res, exec_res)
        
        assert result == "web_search"
        assert sample_shared_store["last_decision"] == exec_res["decision"]
        assert sample_shared_store["next_action"] == "web_search"
        assert sample_shared_store["action_params"]["query"] == "TechCorp news"
        assert "TechCorp news" in sample_shared_store["research_state"]["searches_performed"]
    
    def test_post_read_content_updates(self, node, sample_shared_store):
        """Test post updates for read_content action."""
        exec_res = {
            "decision": {"thinking": "Read page", "action": {"type": "read_content"}},
            "action_type": "read_content",
            "action_params": {"url": "https://example.com"}
        }
        
        result = node.post(sample_shared_store, {}, exec_res)
        
        assert result == "read_content"
        assert "https://example.com" in sample_shared_store["research_state"]["pages_read"]
    
    def test_post_synthesize_updates(self, node, sample_shared_store):
        """Test post updates for synthesize action."""
        exec_res = {
            "decision": {"thinking": "Time to synthesize", "action": {"type": "synthesize"}},
            "action_type": "synthesize",
            "action_params": {}
        }
        
        result = node.post(sample_shared_store, {}, exec_res)
        
        assert result == "synthesize"
        assert sample_shared_store["research_state"]["synthesis_complete"] is True
    
    def test_llm_initialization(self, node):
        """Test that LLM wrapper is initialized."""
        assert node.llm is not None
    
    def test_node_retry_configuration(self, node):
        """Test that node is configured with appropriate retries."""
        assert node.max_retries == 2
        assert node.wait == 1