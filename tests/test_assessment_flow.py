"""
Tests for AssessmentFlow.

Tests the assessment flow including:
- Flow initialization and setup
- Input validation and defaults
- Integration with SuitabilityScoringNode
- Output validation and logging
- Error handling for missing inputs
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging
from typing import Dict, Any

from flow import AssessmentFlow
from nodes import SuitabilityScoringNode


class TestAssessmentFlow:
    """Test suite for AssessmentFlow."""
    
    @pytest.fixture
    def flow(self):
        """Create AssessmentFlow instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return AssessmentFlow()
    
    @pytest.fixture
    def complete_shared_store(self):
        """Complete shared store with all required inputs."""
        return {
            "job_title": "Senior Software Engineer",
            "company_name": "TechCorp Inc",
            "requirements": {
                "required_skills": ["Python", "AWS", "Docker"],
                "preferred_skills": ["Kubernetes", "React"],
                "experience_years": "5+ years"
            },
            "requirement_mapping_final": {
                "required_skills": {
                    "Python": {
                        "evidence": [{"type": "experience"}],
                        "is_gap": False,
                        "strength_summary": "HIGH"
                    },
                    "AWS": {
                        "evidence": [{"type": "experience"}],
                        "is_gap": False,
                        "strength_summary": "MEDIUM"
                    },
                    "Docker": {
                        "evidence": [],
                        "is_gap": True,
                        "strength_summary": "NONE"
                    }
                }
            },
            "gaps": [
                {
                    "requirement": "Docker",
                    "gap_type": "missing",
                    "mitigation_strategy": "Quick learner"
                }
            ],
            "company_research": {
                "culture": ["Innovation", "Remote-first"],
                "technology_stack_practices": ["Python", "AWS"]
            }
        }
    
    @pytest.fixture
    def minimal_shared_store(self):
        """Minimal shared store missing optional fields."""
        return {
            "job_title": "Engineer",
            "company_name": "Company",
            "requirements": {"required_skills": ["Python"]},
            "requirement_mapping_final": {
                "required_skills": {
                    "Python": {"is_gap": False, "strength_summary": "HIGH"}
                }
            },
            "gaps": []
        }
    
    def test_flow_initialization(self, flow):
        """Test flow is properly initialized with SuitabilityScoringNode."""
        assert flow.start_node is not None
        assert isinstance(flow.start_node, SuitabilityScoringNode)
    
    def test_prep_with_complete_inputs(self, flow, complete_shared_store):
        """Test prep with all required inputs present."""
        result = flow.prep(complete_shared_store)
        
        assert result["input_validation"] == "complete"
        # Should not modify the shared store when all inputs present
        assert "requirement_mapping_final" in complete_shared_store
        assert "gaps" in complete_shared_store
        assert "company_research" in complete_shared_store
    
    def test_prep_with_missing_required_fields(self, flow):
        """Test prep initializes missing required fields."""
        shared = {
            "job_title": "Engineer"
            # Missing: company_name, requirements, requirement_mapping_final, gaps
        }
        
        with patch('flow.logger') as mock_logger:
            result = flow.prep(shared)
            
            # Should log warning about missing fields
            mock_logger.warning.assert_called()
            
            # Should initialize missing fields
            assert shared["company_name"] == "Unknown"
            assert shared["requirements"] == {}
            assert shared["requirement_mapping_final"] == {}
            assert shared["gaps"] == []
            assert result["input_validation"] == "complete"
    
    def test_prep_without_company_research(self, flow, minimal_shared_store):
        """Test prep warns when company research is missing."""
        with patch('flow.logger') as mock_logger:
            result = flow.prep(minimal_shared_store)
            
            # Should warn about missing company research
            mock_logger.warning.assert_any_call(
                "No company research available for cultural fit assessment"
            )
            
            # Should initialize empty company research
            assert minimal_shared_store["company_research"] == {}
    
    def test_post_with_successful_assessment(self, flow, complete_shared_store):
        """Test post processing with successful assessment."""
        # Add assessment results
        complete_shared_store["suitability_assessment"] = {
            "technical_fit_score": 75,
            "cultural_fit_score": 85,
            "key_strengths": ["Python expertise", "Cloud experience"],
            "critical_gaps": ["Docker knowledge"],
            "unique_value_proposition": "Strong backend developer",
            "overall_recommendation": "Excellent candidate with strong technical skills..."
        }
        
        with patch('flow.logger') as mock_logger:
            result = flow.post(complete_shared_store, {}, None)
            
            # Should log assessment summary
            mock_logger.info.assert_any_call("SUITABILITY ASSESSMENT COMPLETE")
            mock_logger.info.assert_any_call("Technical Fit Score: 75/100")
            mock_logger.info.assert_any_call("Cultural Fit Score: 85/100")
            mock_logger.info.assert_any_call("Key Strengths: 2")
            mock_logger.info.assert_any_call("Critical Gaps: 1")
            
            # Should return shared store
            assert result == complete_shared_store
    
    def test_post_without_assessment(self, flow, complete_shared_store):
        """Test post handling when assessment is missing."""
        # Remove assessment results
        if "suitability_assessment" in complete_shared_store:
            del complete_shared_store["suitability_assessment"]
        
        with patch('flow.logger') as mock_logger:
            result = flow.post(complete_shared_store, {}, None)
            
            # Should log error
            mock_logger.error.assert_called_with(
                "AssessmentFlow failed to produce suitability assessment"
            )
            
            # Should still return shared store
            assert result == complete_shared_store
    
    def test_full_flow_execution(self, flow, complete_shared_store):
        """Test complete flow execution."""
        # Mock the LLM response
        flow.start_node.llm.call_llm_structured_sync.return_value = {
            "cultural_fit_score": 80,
            "key_strengths": ["Test strength"],
            "critical_gaps": [],
            "unique_value_proposition": "Test value",
            "overall_recommendation": "Test recommendation"
        }
        
        # Run the flow
        with patch('flow.logger'):
            result = flow._run(complete_shared_store)
            
            # Should have assessment in shared store
            assert "suitability_assessment" in complete_shared_store
            assessment = complete_shared_store["suitability_assessment"]
            
            # Technical fit score is calculated, not from LLM
            assert "technical_fit_score" in assessment
            assert assessment["cultural_fit_score"] == 80
            assert assessment["key_strengths"] == ["Test strength"]
    
    def test_flow_with_empty_inputs(self, flow):
        """Test flow handles completely empty inputs gracefully."""
        shared = {}
        
        with patch('flow.logger'):
            # Should not raise exceptions
            flow.prep(shared)
            
            # Should have initialized all required fields
            assert shared["job_title"] == "Unknown"
            assert shared["company_name"] == "Unknown"
            assert shared["requirements"] == {}
            assert shared["requirement_mapping_final"] == {}
            assert shared["gaps"] == []
            assert shared["company_research"] == {}
    
    def test_assessment_data_structure(self, flow):
        """Test the expected assessment data structure."""
        assessment = {
            "technical_fit_score": 85,
            "cultural_fit_score": 90,
            "key_strengths": [
                "Strong Python background",
                "Cloud architecture experience",
                "Remote work alignment"
            ],
            "critical_gaps": [
                "Limited containerization experience"
            ],
            "unique_value_proposition": "Combines technical depth with architectural thinking",
            "overall_recommendation": "Strong candidate - proceed with interview"
        }
        
        # Verify all expected fields are present
        required_fields = [
            "technical_fit_score",
            "cultural_fit_score",
            "key_strengths",
            "critical_gaps",
            "unique_value_proposition",
            "overall_recommendation"
        ]
        
        for field in required_fields:
            assert field in assessment
        
        # Verify data types
        assert isinstance(assessment["technical_fit_score"], int)
        assert isinstance(assessment["cultural_fit_score"], int)
        assert isinstance(assessment["key_strengths"], list)
        assert isinstance(assessment["critical_gaps"], list)
        assert isinstance(assessment["unique_value_proposition"], str)
        assert isinstance(assessment["overall_recommendation"], str)
    
    def test_logging_output_format(self, flow, complete_shared_store):
        """Test the logging output format is correct."""
        complete_shared_store["suitability_assessment"] = {
            "technical_fit_score": 65,
            "cultural_fit_score": 75,
            "key_strengths": ["A", "B", "C"],
            "critical_gaps": ["X", "Y"],
            "overall_recommendation": "This is a very long recommendation that should be truncated in the log output to avoid cluttering the console with too much text that goes on and on..."
        }
        
        logged_messages = []
        
        def capture_log(msg, *args, **kwargs):
            logged_messages.append(msg)
        
        with patch('flow.logger.info', side_effect=capture_log):
            flow.post(complete_shared_store, {}, None)
            
            # Check for divider lines
            assert "=" * 50 in logged_messages
            
            # Check for scores
            assert any("Technical Fit Score: 65/100" in msg for msg in logged_messages)
            assert any("Cultural Fit Score: 75/100" in msg for msg in logged_messages)
            
            # Check for counts
            assert any("Key Strengths: 3" in msg for msg in logged_messages)
            assert any("Critical Gaps: 2" in msg for msg in logged_messages)
            
            # Check recommendation is truncated
            assert any("Recommendation:" in msg and "..." in msg for msg in logged_messages)