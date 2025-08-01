"""
Tests for GapAnalysisNode.

Tests the gap identification and mitigation strategy generation including:
- Identifying requirements with missing or weak evidence
- Generating mitigation strategies via LLM
- Creating final mapping with gap indicators
- Error handling
"""

import pytest
from unittest.mock import Mock, patch
from nodes import GapAnalysisNode


class TestGapAnalysisNode:
    """Test suite for GapAnalysisNode."""
    
    @pytest.fixture
    def node(self):
        """Create a GapAnalysisNode instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return GapAnalysisNode()
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample job requirements."""
        return {
            "required_skills": ["Python", "Docker", "Kubernetes"],
            "preferred_skills": ["Terraform", "AWS"],
            "experience_years": 5,
            "education": "Bachelor's degree in Computer Science"
        }
    
    @pytest.fixture
    def sample_assessed_mapping(self):
        """Sample assessed mapping with various strength levels."""
        return {
            "required_skills": {
                "Python": [
                    {
                        "type": "experience",
                        "title": "Senior Developer",
                        "strength": "HIGH"
                    }
                ],
                "Docker": [
                    {
                        "type": "experience", 
                        "title": "DevOps Role",
                        "strength": "MEDIUM"
                    }
                ],
                "Kubernetes": []  # Missing evidence
            },
            "experience_years": [
                {
                    "type": "summary",
                    "title": "3 years experience",
                    "strength": "LOW"  # Weak evidence
                }
            ],
            "education": []  # Missing evidence
        }
    
    def test_prep_success(self, node, sample_assessed_mapping, sample_requirements):
        """Test successful prep with valid data."""
        shared = {
            "requirement_mapping_assessed": sample_assessed_mapping,
            "requirements": sample_requirements
        }
        
        result = node.prep(shared)
        assert isinstance(result, tuple)
        assert result[0] == sample_assessed_mapping
        assert result[1] == sample_requirements
    
    def test_prep_missing_assessed_mapping(self, node, sample_requirements):
        """Test prep with missing assessed mapping."""
        shared = {"requirements": sample_requirements}
        
        with pytest.raises(ValueError, match="No assessed mapping found"):
            node.prep(shared)
    
    def test_prep_missing_requirements(self, node, sample_assessed_mapping):
        """Test prep with missing requirements."""
        shared = {"requirement_mapping_assessed": sample_assessed_mapping}
        
        with pytest.raises(ValueError, match="No requirements found"):
            node.prep(shared)
    
    def test_exec_identifies_missing_evidence_gaps(self, node, sample_assessed_mapping, sample_requirements):
        """Test identification of requirements with no evidence."""
        node.llm.call_llm_sync.return_value = "Focus on container orchestration experience with Docker Compose and highlight eagerness to expand to Kubernetes."
        
        result = node.exec((sample_assessed_mapping, sample_requirements))
        gaps = result["gaps"]
        
        # Should find Kubernetes (missing) and education (missing)
        assert len(gaps) >= 2
        
        # Check Kubernetes gap
        k8s_gap = next((g for g in gaps if g["requirement"] == "Kubernetes"), None)
        assert k8s_gap is not None
        assert k8s_gap["gap_type"] == "missing"
        assert k8s_gap["category"] == "required_skills"
        assert "mitigation_strategy" in k8s_gap
    
    def test_exec_identifies_weak_evidence_gaps(self, node, sample_assessed_mapping, sample_requirements):
        """Test identification of requirements with only weak evidence."""
        node.llm.call_llm_sync.return_value = "Emphasize rapid career progression and intensive project experience that accelerated learning."
        
        result = node.exec((sample_assessed_mapping, sample_requirements))
        gaps = result["gaps"]
        
        # Should find experience_years (LOW strength)
        exp_gap = next((g for g in gaps if g["category"] == "experience_years"), None)
        assert exp_gap is not None
        assert exp_gap["gap_type"] == "weak"
        assert len(exp_gap["evidence"]) > 0
    
    def test_exec_no_gaps_found(self, node):
        """Test when no gaps are found."""
        assessed_mapping = {
            "required_skills": {
                "Python": [{"strength": "HIGH"}],
                "Docker": [{"strength": "MEDIUM"}]
            }
        }
        requirements = {
            "required_skills": ["Python", "Docker"]
        }
        
        result = node.exec((assessed_mapping, requirements))
        assert result["gaps"] == []
    
    def test_exec_creates_final_mapping(self, node, sample_assessed_mapping, sample_requirements):
        """Test creation of final mapping with gap indicators."""
        node.llm.call_llm_sync.return_value = "Test strategy"
        
        result = node.exec((sample_assessed_mapping, sample_requirements))
        final_mapping = result["requirement_mapping_final"]
        
        # Check structure
        assert "required_skills" in final_mapping
        assert "Python" in final_mapping["required_skills"]
        
        # Python should not be a gap (HIGH strength)
        python_data = final_mapping["required_skills"]["Python"]
        assert python_data["is_gap"] is False
        assert python_data["strength_summary"] == "HIGH"
        
        # Kubernetes should be a gap (no evidence)
        k8s_data = final_mapping["required_skills"]["Kubernetes"]
        assert k8s_data["is_gap"] is True
        assert k8s_data["strength_summary"] == "NONE"
    
    def test_exec_handles_llm_error(self, node, sample_assessed_mapping, sample_requirements):
        """Test handling of LLM errors during strategy generation."""
        node.llm.call_llm_sync.side_effect = Exception("LLM API error")
        
        with patch('nodes.logger') as mock_logger:
            result = node.exec((sample_assessed_mapping, sample_requirements))
            gaps = result["gaps"]
            
            # Should still identify gaps with default strategy
            assert len(gaps) > 0
            assert all("mitigation_strategy" in gap for gap in gaps)
            assert gaps[0]["mitigation_strategy"] == "Highlight transferable skills and demonstrate strong learning ability and enthusiasm for this area."
            mock_logger.error.assert_called()
    
    def test_generate_mitigation_strategy_prompt(self, node):
        """Test the prompt construction for mitigation strategies."""
        gap = {
            "requirement": "Kubernetes",
            "category": "required_skills",
            "gap_type": "missing",
            "evidence": []
        }
        
        node.llm.call_llm_sync.return_value = "Test strategy"
        
        strategy = node._generate_mitigation_strategy(gap)
        
        # Verify prompt was called
        node.llm.call_llm_sync.assert_called_once()
        prompt = node.llm.call_llm_sync.call_args[0][0]
        
        # Check prompt contains key elements
        assert "Kubernetes" in prompt
        assert "required_skills" in prompt
        assert "missing" in prompt
        assert "no evidence found" in prompt
        assert "transferable skills" in prompt
    
    def test_summarize_strength_various_cases(self, node):
        """Test strength summarization logic."""
        # No evidence
        assert node._summarize_strength([]) == "NONE"
        
        # All HIGH
        assert node._summarize_strength([
            {"strength": "HIGH"},
            {"strength": "HIGH"}
        ]) == "HIGH"
        
        # Mixed with HIGH
        assert node._summarize_strength([
            {"strength": "HIGH"},
            {"strength": "MEDIUM"},
            {"strength": "LOW"}
        ]) == "HIGH"
        
        # MEDIUM and LOW
        assert node._summarize_strength([
            {"strength": "MEDIUM"},
            {"strength": "LOW"}
        ]) == "MEDIUM"
        
        # All LOW
        assert node._summarize_strength([
            {"strength": "LOW"},
            {"strength": "LOW"}
        ]) == "LOW"
    
    def test_post_stores_results(self, node):
        """Test that post stores results correctly."""
        shared = {}
        exec_res = {
            "requirement_mapping_final": {"final": "mapping"},
            "gaps": [{"gap": "data"}]
        }
        
        result = node.post(shared, None, exec_res)
        
        assert shared["requirement_mapping_final"] == {"final": "mapping"}
        assert shared["gaps"] == [{"gap": "data"}]
        assert result == "default"
    
    def test_identify_gaps_all_categories(self, node):
        """Test gap identification across all must-have categories."""
        assessed_mapping = {
            "required_skills": {
                "Python": [],  # Missing
                "Docker": [{"strength": "LOW"}]  # Weak
            },
            "experience_years": [],  # Missing
            "education": [{"strength": "LOW"}],  # Weak
            "certifications": []  # Missing
        }
        
        requirements = {
            "required_skills": ["Python", "Docker"],
            "experience_years": 5,
            "education": "BS CS",
            "certifications": "AWS Certified"
        }
        
        gaps = node._identify_gaps(assessed_mapping, requirements)
        
        # Should find gaps in all categories
        assert len(gaps) == 5  # Python, Docker, exp_years, education, certifications
        
        gap_categories = [g["category"] for g in gaps]
        assert "required_skills" in gap_categories
        assert "experience_years" in gap_categories
        assert "education" in gap_categories
        assert "certifications" in gap_categories
    
    def test_final_mapping_single_value_requirements(self, node):
        """Test final mapping creation for single value requirements."""
        assessed_mapping = {
            "experience_years": [
                {"strength": "MEDIUM", "type": "summary"}
            ],
            "education": []
        }
        
        final_mapping = node._create_final_mapping(assessed_mapping)
        
        # Experience years (has MEDIUM evidence)
        assert final_mapping["experience_years"]["is_gap"] is False
        assert final_mapping["experience_years"]["strength_summary"] == "MEDIUM"
        
        # Education (no evidence)
        assert final_mapping["education"]["is_gap"] is True
        assert final_mapping["education"]["strength_summary"] == "NONE"
    
    def test_llm_initialization(self, node):
        """Test that LLM wrapper is initialized."""
        assert node.llm is not None
    
    def test_node_retry_configuration(self, node):
        """Test that node is configured with appropriate retries."""
        assert node.max_retries == 2
        assert node.wait == 1