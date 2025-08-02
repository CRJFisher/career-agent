"""
Tests for CompanyResearchAgent flow.

Tests the research agent orchestration including:
- Flow initialization and graph construction
- Action routing to appropriate nodes
- Iterative research process
- Loop termination conditions
- Maximum iteration safety
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from flow import CompanyResearchAgent
from nodes import DecideActionNode, WebSearchNode, ReadContentNode, SynthesizeInfoNode


class TestCompanyResearchAgent:
    """Test suite for CompanyResearchAgent flow."""
    
    @pytest.fixture
    def agent(self):
        """Create CompanyResearchAgent instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return CompanyResearchAgent(max_iterations=10)
    
    @pytest.fixture
    def sample_shared_store(self):
        """Sample shared store for research."""
        return {
            "company_name": "TechCorp Inc",
            "job_title": "Senior Software Engineer"
        }
    
    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.max_iterations == 10
        assert agent.iteration_count == 0
        assert agent.start_node is not None
        assert isinstance(agent.start_node, DecideActionNode)
    
    def test_node_connections(self, agent):
        """Test that all nodes are properly connected."""
        decide = agent.start_node
        
        # Check that decide node has connections to tool nodes
        assert "web_search" in decide.successors
        assert "read_content" in decide.successors
        assert "synthesize" in decide.successors
        
        # Check that tool nodes connect back to decide
        web_search = decide.successors["web_search"]
        read_content = decide.successors["read_content"]
        synthesize = decide.successors["synthesize"]
        
        assert isinstance(web_search, WebSearchNode)
        assert isinstance(read_content, ReadContentNode)
        assert isinstance(synthesize, SynthesizeInfoNode)
        
        # Verify return paths
        assert "decide" in web_search.successors
        assert web_search.successors["decide"] == decide
        assert "decide" in read_content.successors
        assert read_content.successors["decide"] == decide
        assert "decide" in synthesize.successors
        assert synthesize.successors["decide"] == decide
    
    def test_prep_initializes_research_template(self, agent, sample_shared_store):
        """Test prep initializes research template."""
        result = agent.prep(sample_shared_store)
        
        assert "company_research" in sample_shared_store
        assert sample_shared_store["company_research"]["mission"] is None
        assert sample_shared_store["company_research"]["culture"] is None
        assert result["max_iterations"] == 10
        assert agent.iteration_count == 0
    
    def test_prep_preserves_existing_research(self, agent):
        """Test prep preserves existing research data."""
        shared = {
            "company_name": "TechCorp",
            "company_research": {
                "mission": "Existing mission data",
                "culture": None
            }
        }
        
        agent.prep(shared)
        
        # Should preserve existing data
        assert shared["company_research"]["mission"] == "Existing mission data"
        assert shared["company_research"]["culture"] is None
    
    def test_get_next_node_routing(self, agent):
        """Test get_next_node routes actions correctly."""
        decide = agent.start_node
        
        # Test routing to web_search
        next_node = agent.get_next_node(decide, "web_search")
        assert isinstance(next_node, WebSearchNode)
        assert agent.iteration_count == 1
        
        # Test routing to read_content
        next_node = agent.get_next_node(decide, "read_content")
        assert isinstance(next_node, ReadContentNode)
        assert agent.iteration_count == 2
        
        # Test routing to synthesize
        next_node = agent.get_next_node(decide, "synthesize")
        assert isinstance(next_node, SynthesizeInfoNode)
        assert agent.iteration_count == 3
    
    def test_get_next_node_finish_action(self, agent):
        """Test get_next_node handles finish action."""
        decide = agent.start_node
        
        next_node = agent.get_next_node(decide, "finish")
        assert next_node is None
        assert agent.iteration_count == 1
    
    def test_get_next_node_max_iterations(self, agent):
        """Test get_next_node enforces max iterations."""
        decide = agent.start_node
        
        # Set iteration count to max - 2 (since get_next_node increments first)
        agent.iteration_count = 8
        
        # Should allow one more iteration (will increment to 9)
        next_node = agent.get_next_node(decide, "web_search")
        assert next_node is not None
        assert agent.iteration_count == 9
        
        # Should block at max iterations (will increment to 10)
        next_node = agent.get_next_node(decide, "web_search")
        assert next_node is None
    
    def test_get_next_node_unknown_action(self, agent):
        """Test get_next_node handles unknown actions."""
        decide = agent.start_node
        
        # Should warn and return None for unknown action
        with patch('flow.logger') as mock_logger:
            next_node = agent.get_next_node(decide, "unknown_action")
            assert next_node is None
            # PocketFlow's Flow class logs the warning
    
    @patch.object(DecideActionNode, '_run')
    @patch.object(WebSearchNode, '_run')
    @patch.object(SynthesizeInfoNode, '_run')
    def test_simple_research_flow(self, mock_synthesize, mock_search, mock_decide, agent, sample_shared_store):
        """Test a simple research flow execution."""
        # Mock decide node to search, then synthesize, then finish
        mock_decide.side_effect = ["web_search", "synthesize", "finish"]
        
        # Mock tool nodes to return to decide
        mock_search.return_value = "decide"
        mock_synthesize.return_value = "decide"
        
        # Run the flow
        result = agent._run(sample_shared_store)
        
        # Verify execution order
        assert mock_decide.call_count == 3
        assert mock_search.call_count == 1
        assert mock_synthesize.call_count == 1
        
        # Verify research template was initialized
        assert "company_research" in sample_shared_store
    
    @patch.object(DecideActionNode, '_run')
    def test_max_iterations_safety(self, mock_decide, agent, sample_shared_store):
        """Test that max iterations prevents infinite loops."""
        # Mock decide to always return web_search (infinite loop)
        mock_decide.return_value = "web_search"
        
        # Create agent with low max iterations
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            agent = CompanyResearchAgent(max_iterations=3)
        
            # Run should terminate after max iterations
            with patch.object(WebSearchNode, '_run', return_value="decide"):
                result = agent._run(sample_shared_store)
        
            # Should have hit the limit
            assert agent.iteration_count >= 3
    
    def test_integration_with_real_nodes(self, agent, sample_shared_store):
        """Test integration with real node implementations (mocked utilities)."""
        # Mock the LLM and utilities
        with patch('nodes.get_default_llm_wrapper') as mock_llm_wrapper:
            mock_llm = Mock()
            mock_llm_wrapper.return_value = mock_llm
            
            # Mock decide node to finish immediately
            mock_llm.call_llm_sync.return_value = """
thinking: |
  No research needed for this test.
  
action:
  type: finish
  parameters: {}
"""
            
            # Recreate agent to use mocked LLM
            agent = CompanyResearchAgent(max_iterations=5)
            
            # Run the flow
            result = agent._run(sample_shared_store)
            
            # Should have initialized research template
            assert "company_research" in sample_shared_store
            
            # Should have called LLM at least once
            assert mock_llm.call_llm_sync.called
    
    def test_research_template_structure(self, agent, sample_shared_store):
        """Test that research template has all required fields."""
        agent.prep(sample_shared_store)
        
        research = sample_shared_store["company_research"]
        
        # Check all required fields exist
        required_fields = [
            "mission",
            "team_scope", 
            "strategic_importance",
            "culture",
            "technology_stack_practices",
            "recent_developments",
            "market_position_growth"
        ]
        
        for field in required_fields:
            assert field in research
            assert research[field] is None  # Initially None
    
    def test_node_action_returns(self):
        """Test that tool nodes return correct actions."""
        # This verifies our implementation matches the flow expectations
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            web_search = WebSearchNode()
            read_content = ReadContentNode()
            synthesize = SynthesizeInfoNode()
        
            # All tool nodes should return "decide" to loop back
            shared = {"search_results": [], "action_params": {"query": "test"}}
            assert web_search.post(shared, {}, []) == "decide"
            
            shared = {"current_content": "content", "action_params": {"url": "http://test.com"}}
            prep_res = {"url": "http://test.com", "focus": ""}
            assert read_content.post(shared, prep_res, "content") == "decide"
            
            shared = {"company_research": {}}
            assert synthesize.post(shared, {}, {}) == "decide"