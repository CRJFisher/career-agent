"""
Tests for SuitabilityScoringNode.

Tests the suitability assessment functionality including:
- Technical fit score calculation
- Cultural fit assessment
- Strengths and gaps identification
- Unique value proposition generation
- LLM integration and error handling
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from nodes import SuitabilityScoringNode


class TestSuitabilityScoringNode:
    """Test suite for SuitabilityScoringNode."""
    
    @pytest.fixture
    def node(self):
        """Create SuitabilityScoringNode instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return SuitabilityScoringNode()
    
    @pytest.fixture
    def sample_shared_store(self):
        """Sample shared store with assessment inputs."""
        return {
            "job_title": "Senior Software Engineer",
            "company_name": "TechCorp Inc",
            "requirements": {
                "required_skills": ["Python", "AWS", "Docker", "REST APIs"],
                "preferred_skills": ["Kubernetes", "React"],
                "experience_years": "5+ years",
                "education": "Bachelor's in CS or equivalent"
            },
            "requirement_mapping_final": {
                "required_skills": {
                    "Python": {
                        "evidence": [{"type": "experience", "title": "Backend Developer"}],
                        "is_gap": False,
                        "strength_summary": "HIGH"
                    },
                    "AWS": {
                        "evidence": [{"type": "experience", "title": "Cloud Engineer"}],
                        "is_gap": False,
                        "strength_summary": "MEDIUM"
                    },
                    "Docker": {
                        "evidence": [],
                        "is_gap": True,
                        "strength_summary": "NONE"
                    },
                    "REST APIs": {
                        "evidence": [{"type": "project", "title": "API Platform"}],
                        "is_gap": False,
                        "strength_summary": "HIGH"
                    }
                },
                "preferred_skills": {
                    "Kubernetes": {
                        "evidence": [],
                        "is_gap": True,
                        "strength_summary": "NONE"
                    },
                    "React": {
                        "evidence": [{"type": "project", "title": "Dashboard"}],
                        "is_gap": False,
                        "strength_summary": "LOW"
                    }
                }
            },
            "gaps": [
                {
                    "requirement": "Docker",
                    "category": "required_skills",
                    "gap_type": "missing",
                    "mitigation_strategy": "Highlight containerization interest and quick learning ability"
                },
                {
                    "requirement": "Kubernetes",
                    "category": "preferred_skills",
                    "gap_type": "missing",
                    "mitigation_strategy": "Emphasize cloud platform experience"
                }
            ],
            "company_research": {
                "culture": ["Innovation-focused", "Remote-first", "Collaborative"],
                "technology_stack_practices": ["Python", "AWS", "Microservices"],
                "team_work_environment": ["Agile", "Cross-functional teams"]
            }
        }
    
    def test_prep_success(self, node, sample_shared_store):
        """Test successful prep with all required data."""
        result = node.prep(sample_shared_store)
        
        assert "requirement_mapping" in result
        assert "gaps" in result
        assert "company_research" in result
        assert result["job_title"] == "Senior Software Engineer"
        assert result["company_name"] == "TechCorp Inc"
        assert len(result["gaps"]) == 2
    
    def test_prep_missing_mapping(self, node):
        """Test prep with missing requirement mapping."""
        shared = {
            "job_title": "Engineer",
            "company_name": "Company",
            "gaps": [],
            "company_research": {}
        }
        
        with pytest.raises(ValueError, match="No requirement mapping found"):
            node.prep(shared)
    
    def test_calculate_technical_fit_perfect_score(self, node):
        """Test technical fit calculation with perfect score."""
        mapping = {
            "required_skills": {
                "Python": {"is_gap": False, "strength_summary": "HIGH"},
                "AWS": {"is_gap": False, "strength_summary": "HIGH"}
            },
            "preferred_skills": {
                "React": {"is_gap": False, "strength_summary": "HIGH"}
            }
        }
        requirements = {
            "required_skills": ["Python", "AWS"],
            "preferred_skills": ["React"]
        }
        
        score = node._calculate_technical_fit(mapping, requirements)
        assert score == 80  # 60 (required) + 20 (preferred)
    
    def test_calculate_technical_fit_mixed_strengths(self, node):
        """Test technical fit with mixed strength levels."""
        mapping = {
            "required_skills": {
                "Python": {"is_gap": False, "strength_summary": "HIGH"},    # 30 points
                "AWS": {"is_gap": False, "strength_summary": "MEDIUM"},     # 18 points
                "Docker": {"is_gap": True, "strength_summary": "NONE"},     # 0 points
                "APIs": {"is_gap": False, "strength_summary": "LOW"}        # 9 points
            }
        }
        requirements = {
            "required_skills": ["Python", "AWS", "Docker", "APIs"]
        }
        
        score = node._calculate_technical_fit(mapping, requirements)
        # Each skill is 15 points (60/4): HIGH=15, MEDIUM=9, LOW=4.5, Missing=0
        # Python: 15, AWS: 9, Docker: 0, APIs: 4.5 = 28.5 rounded to 28
        assert score == 28
    
    def test_calculate_technical_fit_with_other_categories(self, node):
        """Test technical fit including experience/education categories."""
        mapping = {
            "required_skills": {},
            "experience_years": {"is_gap": False, "strength_summary": "HIGH"},
            "education": {"is_gap": False, "strength_summary": "MEDIUM"}
        }
        requirements = {
            "required_skills": [],
            "experience_years": "5+ years",
            "education": "Bachelor's"
        }
        
        score = node._calculate_technical_fit(mapping, requirements)
        # No required/preferred skills = 60+20 = 80 points by default
        # Experience: 20/3 = 6.67, Education: 20/3 * 0.6 = 4, Total: 10.67
        # But since there are no skills requirements, it gets full 60+20 for skills
        assert score == 70  # 60 (required default) + 10 (other categories)
    
    def test_score_category(self, node):
        """Test category scoring logic."""
        requirements = ["Python", "AWS", "Docker"]
        mappings = {
            "Python": {"is_gap": False, "strength_summary": "HIGH"},
            "AWS": {"is_gap": False, "strength_summary": "MEDIUM"},
            "Docker": {"is_gap": True, "strength_summary": "NONE"}
        }
        
        score = node._score_category(requirements, mappings, 60)
        # Python: 20, AWS: 12, Docker: 0 = 32
        assert score == 32
    
    def test_exec_success(self, node, sample_shared_store):
        """Test successful execution with LLM response."""
        context = node.prep(sample_shared_store)
        
        # Mock LLM response
        node.llm.call_llm_structured_sync.return_value = {
            "cultural_fit_score": 85,
            "key_strengths": [
                "Strong Python expertise with cloud experience",
                "API design and implementation skills",
                "Remote work experience aligns with company culture"
            ],
            "critical_gaps": [
                "Missing Docker containerization experience",
                "Limited Kubernetes knowledge"
            ],
            "unique_value_proposition": "Combines deep backend expertise with cloud architecture skills...",
            "overall_recommendation": "Strong candidate worth pursuing..."
        }
        
        result = node.exec(context)
        
        assert result["technical_fit_score"] == 42  # Calculated from sample data
        assert result["cultural_fit_score"] == 85
        assert len(result["key_strengths"]) == 3
        assert len(result["critical_gaps"]) == 2
        assert "unique_value_proposition" in result
        assert "overall_recommendation" in result
    
    def test_exec_missing_fields(self, node, sample_shared_store):
        """Test exec handling missing fields in LLM response."""
        context = node.prep(sample_shared_store)
        
        # Mock incomplete LLM response
        node.llm.call_llm_structured_sync.return_value = {
            "cultural_fit_score": 75,
            "key_strengths": ["Good technical skills"]
            # Missing other required fields
        }
        
        result = node.exec(context)
        
        # Should fill in missing fields with defaults
        assert result["technical_fit_score"] == 42
        assert result["cultural_fit_score"] == 75
        assert result["critical_gaps"] == []  # Default empty list
        assert result["unique_value_proposition"] == "Unable to assess"
        assert result["overall_recommendation"] == "Unable to assess"
    
    def test_exec_llm_failure(self, node, sample_shared_store):
        """Test exec with LLM failure."""
        context = node.prep(sample_shared_store)
        
        # Mock LLM error
        node.llm.call_llm_structured_sync.side_effect = Exception("LLM error")
        
        result = node.exec(context)
        
        # Should return minimal assessment
        assert result["technical_fit_score"] == 42
        assert result["cultural_fit_score"] == 50
        assert result["key_strengths"] == ["Technical skills match requirements"]
        assert result["critical_gaps"] == ["Unable to perform full assessment"]
        assert result["unique_value_proposition"] == "Candidate shows potential"
        assert result["overall_recommendation"] == "Requires further evaluation"
    
    def test_post_updates_shared(self, node, sample_shared_store):
        """Test post updates shared store correctly."""
        prep_res = {}
        exec_res = {
            "technical_fit_score": 75,
            "cultural_fit_score": 80,
            "key_strengths": ["Strength 1", "Strength 2"],
            "critical_gaps": ["Gap 1"],
            "unique_value_proposition": "Unique value",
            "overall_recommendation": "Recommend"
        }
        
        result = node.post(sample_shared_store, prep_res, exec_res)
        
        assert result == "default"
        assert sample_shared_store["suitability_assessment"] == exec_res
    
    def test_build_assessment_prompt(self, node):
        """Test assessment prompt construction."""
        context = {
            "job_title": "Engineer",
            "company_name": "TechCorp",
            "requirement_mapping": {
                "required_skills": {
                    "Python": {"strength_summary": "HIGH"},
                    "AWS": {"strength_summary": "MEDIUM"}
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
                "culture": ["Innovation", "Remote"],
                "technology_stack_practices": ["Python", "Cloud"]
            },
            "requirements": {}
        }
        
        prompt = node._build_assessment_prompt(context, 75)
        
        # Check key elements in prompt
        assert "Engineer" in prompt
        assert "TechCorp" in prompt
        assert "75/100" in prompt
        assert "Python" in prompt
        assert "Docker (missing)" in prompt
        assert "Innovation" in prompt
        assert "cultural_fit_score:" in prompt
        assert "unique_value_proposition:" in prompt
    
    def test_summarize_mapping(self, node):
        """Test requirement mapping summarization."""
        mapping = {
            "required_skills": {
                "Python": {"strength_summary": "HIGH"},
                "AWS": {"strength_summary": "HIGH"},
                "Docker": {"strength_summary": "MEDIUM"},
                "API": {"strength_summary": "LOW"}
            },
            "preferred_skills": {
                "React": {"strength_summary": "MEDIUM"}
            }
        }
        
        summary = node._summarize_mapping(mapping)
        
        assert "required_skills: 2 HIGH, 1 MEDIUM out of 4" in summary
        assert "preferred_skills: 0 HIGH, 1 MEDIUM out of 1" in summary
    
    def test_summarize_gaps(self, node):
        """Test gap summarization."""
        gaps = [
            {
                "requirement": "Docker",
                "gap_type": "missing",
                "mitigation_strategy": "Emphasize containers knowledge"
            },
            {
                "requirement": "5+ years",
                "gap_type": "weak",
                "mitigation_strategy": ""
            }
        ]
        
        summary = node._summarize_gaps(gaps)
        
        assert "Docker (missing)" in summary
        assert "Mitigation: Emphasize containers knowledge" in summary
        assert "5+ years (weak)" in summary
    
    def test_summarize_company_research(self, node):
        """Test company research summarization."""
        research = {
            "culture": ["Remote-first", "Innovation", "Work-life balance", "Open source"],
            "technology_stack_practices": ["Python", "Kubernetes", "Microservices"],
            "team_work_environment": ["Agile", "Autonomous teams"]
        }
        
        summary = node._summarize_company_research(research)
        
        # Should include first 3 items of each category
        assert "Culture: Remote-first, Innovation, Work-life balance" in summary
        assert "Tech Stack: Python, Kubernetes, Microservices" in summary
        assert "Work Environment: Agile, Autonomous teams" in summary
    
    def test_empty_inputs(self, node):
        """Test handling of empty inputs."""
        # Empty mapping summary
        assert node._summarize_mapping({}) == "No mapping data available"
        
        # Empty gaps summary
        assert node._summarize_gaps([]) == "No critical gaps identified"
        
        # Empty research summary
        assert node._summarize_company_research({}) == "No company research available"
        
        # Score category with no requirements
        assert node._score_category([], {}, 60) == 60