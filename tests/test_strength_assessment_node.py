"""
Tests for StrengthAssessmentNode.

Tests the LLM-based strength assessment functionality including:
- Evidence strength scoring (HIGH/MEDIUM/LOW)
- Handling various mapping structures
- LLM interaction and response validation
- Error handling
"""

import pytest
from unittest.mock import Mock, patch
from nodes import StrengthAssessmentNode


class TestStrengthAssessmentNode:
    """Test suite for StrengthAssessmentNode."""
    
    @pytest.fixture
    def node(self):
        """Create a StrengthAssessmentNode instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return StrengthAssessmentNode()
    
    @pytest.fixture
    def sample_mapping(self):
        """Sample requirement mapping from RequirementMappingNode."""
        return {
            "required_skills": {
                "Python": [
                    {
                        "type": "experience",
                        "title": "Senior Software Engineer",
                        "match_type": "exact",
                        "source": {"company": "TechCorp"}
                    },
                    {
                        "type": "skills",
                        "title": "Skills",
                        "match_type": "exact",
                        "source": {}
                    }
                ],
                "Docker": [
                    {
                        "type": "experience",
                        "title": "DevOps Engineer",
                        "match_type": "partial",
                        "source": {"company": "StartupXYZ"}
                    }
                ],
                "Kubernetes": []  # No evidence found
            },
            "education": [  # Single value requirement
                {
                    "type": "experience",
                    "title": "Software Developer",
                    "match_type": "partial",
                    "source": {}
                }
            ]
        }
    
    def test_prep_success(self, node, sample_mapping):
        """Test successful prep with valid mapping."""
        shared = {"requirement_mapping_raw": sample_mapping}
        
        result = node.prep(shared)
        assert result == sample_mapping
    
    def test_prep_missing_mapping(self, node):
        """Test prep with missing requirement mapping."""
        shared = {}
        
        with pytest.raises(ValueError, match="No requirement mapping found"):
            node.prep(shared)
    
    def test_prep_empty_mapping(self, node):
        """Test prep with empty requirement mapping."""
        shared = {"requirement_mapping_raw": {}}
        
        with pytest.raises(ValueError, match="No requirement mapping found"):
            node.prep(shared)
    
    def test_exec_assigns_high_score(self, node, sample_mapping):
        """Test that exact matches get HIGH scores."""
        # Mock LLM to return HIGH for exact matches
        node.llm.call_llm_sync.return_value = "HIGH"
        
        result = node.exec(sample_mapping)
        assessed = result["requirement_mapping_assessed"]
        
        # Check Python evidence (exact match) got HIGH
        python_evidence = assessed["required_skills"]["Python"]
        assert all(e["strength"] == "HIGH" for e in python_evidence)
        assert len(python_evidence) == 2
        
        # Verify original evidence is preserved
        assert python_evidence[0]["type"] == "experience"
        assert python_evidence[0]["match_type"] == "exact"
    
    def test_exec_assigns_medium_score(self, node, sample_mapping):
        """Test that partial matches get appropriate scores."""
        # Mock LLM to return MEDIUM for partial matches
        def mock_llm_response(prompt):
            if "partial" in prompt.lower():
                return "MEDIUM"
            return "HIGH"
        
        node.llm.call_llm_sync.side_effect = mock_llm_response
        
        result = node.exec(sample_mapping)
        assessed = result["requirement_mapping_assessed"]
        
        # Check Docker evidence (partial match) got MEDIUM
        docker_evidence = assessed["required_skills"]["Docker"]
        assert docker_evidence[0]["strength"] == "MEDIUM"
    
    def test_exec_handles_empty_evidence(self, node, sample_mapping):
        """Test handling of requirements with no evidence."""
        result = node.exec(sample_mapping)
        assessed = result["requirement_mapping_assessed"]
        
        # Kubernetes has no evidence
        assert assessed["required_skills"]["Kubernetes"] == []
    
    def test_exec_handles_single_value_requirements(self, node, sample_mapping):
        """Test handling of single value requirements."""
        node.llm.call_llm_sync.return_value = "MEDIUM"
        
        result = node.exec(sample_mapping)
        assessed = result["requirement_mapping_assessed"]
        
        # Education is a single value requirement
        education_evidence = assessed["education"]
        assert len(education_evidence) == 1
        assert education_evidence[0]["strength"] == "MEDIUM"
        assert education_evidence[0]["type"] == "experience"
    
    def test_exec_validates_llm_response(self, node):
        """Test validation of LLM responses."""
        mapping = {
            "skills": {
                "Python": [{"type": "test", "title": "Test", "match_type": "exact"}]
            }
        }
        
        # Test invalid response
        node.llm.call_llm_sync.return_value = "INVALID"
        
        with patch('nodes.logger') as mock_logger:
            result = node.exec(mapping)
            assessed = result["requirement_mapping_assessed"]
            
            # Should default to MEDIUM and log warning
            assert assessed["skills"]["Python"][0]["strength"] == "MEDIUM"
            mock_logger.warning.assert_called_once()
    
    def test_exec_handles_llm_error(self, node):
        """Test handling of LLM errors."""
        mapping = {
            "skills": {
                "Python": [{"type": "test", "title": "Test", "match_type": "exact"}]
            }
        }
        
        # Mock LLM to raise error
        node.llm.call_llm_sync.side_effect = Exception("LLM API error")
        
        with patch('nodes.logger') as mock_logger:
            result = node.exec(mapping)
            assessed = result["requirement_mapping_assessed"]
            
            # Should default to MEDIUM and log error
            assert assessed["skills"]["Python"][0]["strength"] == "MEDIUM"
            mock_logger.error.assert_called_once()
    
    def test_exec_case_insensitive_scores(self, node):
        """Test that scores are case-insensitive."""
        mapping = {
            "skills": {
                "Python": [{"type": "test", "title": "Test", "match_type": "exact"}]
            }
        }
        
        # Return lowercase
        node.llm.call_llm_sync.return_value = "high"
        
        result = node.exec(mapping)
        assessed = result["requirement_mapping_assessed"]
        
        assert assessed["skills"]["Python"][0]["strength"] == "HIGH"
    
    def test_exec_preserves_evidence_structure(self, node, sample_mapping):
        """Test that original evidence structure is preserved."""
        node.llm.call_llm_sync.return_value = "HIGH"
        
        result = node.exec(sample_mapping)
        assessed = result["requirement_mapping_assessed"]
        
        # Check that all original fields are preserved
        python_evidence = assessed["required_skills"]["Python"][0]
        assert "type" in python_evidence
        assert "title" in python_evidence
        assert "match_type" in python_evidence
        assert "source" in python_evidence
        assert "strength" in python_evidence  # New field added
    
    def test_post_stores_results(self, node, sample_mapping):
        """Test that post stores results correctly."""
        shared = {}
        exec_res = {
            "requirement_mapping_assessed": {"test": "mapping"}
        }
        
        result = node.post(shared, sample_mapping, exec_res)
        
        assert shared["requirement_mapping_assessed"] == {"test": "mapping"}
        assert result == "default"
    
    def test_assess_evidence_strength_prompt(self, node):
        """Test the prompt construction for evidence assessment."""
        requirement = "Python programming"
        evidence = {
            "type": "experience",
            "title": "Senior Python Developer",
            "match_type": "exact"
        }
        
        node.llm.call_llm_sync.return_value = "HIGH"
        
        strength = node._assess_evidence_strength(requirement, evidence)
        
        # Verify prompt was called
        node.llm.call_llm_sync.assert_called_once()
        prompt = node.llm.call_llm_sync.call_args[0][0]
        
        # Check prompt contains key elements
        assert "Python programming" in prompt
        assert "experience" in prompt
        assert "Senior Python Developer" in prompt
        assert "exact" in prompt
        assert "HIGH" in prompt
        assert "MEDIUM" in prompt
        assert "LOW" in prompt
    
    def test_llm_initialization(self, node):
        """Test that LLM wrapper is initialized."""
        assert node.llm is not None
    
    def test_node_retry_configuration(self, node):
        """Test that node is configured with appropriate retries."""
        assert node.max_retries == 2
        assert node.wait == 1
    
    def test_exec_complex_mapping(self, node):
        """Test handling of complex nested mappings."""
        complex_mapping = {
            "required_skills": {
                "Python": [
                    {"type": "exp", "title": "Job1", "match_type": "exact"},
                    {"type": "proj", "title": "Proj1", "match_type": "partial"}
                ],
                "Docker": []
            },
            "preferred_skills": {
                "AWS": [
                    {"type": "cert", "title": "AWS Cert", "match_type": "exact"}
                ]
            },
            "responsibilities": {
                "primary": [
                    {"type": "exp", "title": "Lead Dev", "match_type": "partial"}
                ]
            },
            "experience_years": [
                {"type": "summary", "title": "10 years", "match_type": "exact"}
            ]
        }
        
        # Mock different responses
        responses = ["HIGH", "MEDIUM", "HIGH", "MEDIUM", "LOW"]
        node.llm.call_llm_sync.side_effect = responses
        
        result = node.exec(complex_mapping)
        assessed = result["requirement_mapping_assessed"]
        
        # Verify structure is maintained
        assert "required_skills" in assessed
        assert "preferred_skills" in assessed
        assert "responsibilities" in assessed
        assert "experience_years" in assessed
        
        # Verify scores were assigned
        assert assessed["required_skills"]["Python"][0]["strength"] == "HIGH"
        assert assessed["required_skills"]["Python"][1]["strength"] == "MEDIUM"
        assert assessed["preferred_skills"]["AWS"][0]["strength"] == "HIGH"
        assert assessed["responsibilities"]["primary"][0]["strength"] == "MEDIUM"
        assert assessed["experience_years"][0]["strength"] == "LOW"