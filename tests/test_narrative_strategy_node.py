"""
Tests for NarrativeStrategyNode.

Tests the LLM-driven narrative strategy synthesis for job applications.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from nodes import NarrativeStrategyNode


class TestNarrativeStrategyNode:
    """Test suite for NarrativeStrategyNode."""
    
    @pytest.fixture
    def node(self):
        """Create node instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return NarrativeStrategyNode()
    
    @pytest.fixture
    def prioritized_experiences(self):
        """Create sample prioritized experiences."""
        return [
            {
                "rank": 1,
                "title": "Senior Software Engineer",
                "type": "professional",
                "composite_score": 85.5,
                "scores": {
                    "relevance": 90.0,
                    "recency": 100.0,
                    "impact": 80.0,
                    "uniqueness": 60.0,
                    "growth": 70.0
                },
                "data": {
                    "role": "Senior Software Engineer",
                    "company": "TechCorp",
                    "achievements": [
                        "Led team of 5 to deliver microservices platform",
                        "Reduced API latency by 40%"
                    ],
                    "technologies": ["Python", "AWS", "Kubernetes"]
                }
            },
            {
                "rank": 2,
                "title": "ML Pipeline Automation",
                "type": "project",
                "composite_score": 78.0,
                "scores": {
                    "relevance": 85.0,
                    "recency": 90.0,
                    "impact": 75.0,
                    "uniqueness": 80.0,
                    "growth": 40.0
                },
                "data": {
                    "name": "ML Pipeline Automation",
                    "description": "Automated ML model training and deployment",
                    "impact": "Reduced deployment time from days to hours",
                    "technologies": ["Python", "Kubernetes", "MLflow"]
                }
            },
            {
                "rank": 3,
                "title": "Software Engineer",
                "type": "professional",
                "composite_score": 65.0,
                "scores": {
                    "relevance": 70.0,
                    "recency": 60.0,
                    "impact": 60.0,
                    "uniqueness": 50.0,
                    "growth": 60.0
                },
                "data": {
                    "role": "Software Engineer",
                    "company": "StartupXYZ",
                    "achievements": [
                        "Built REST APIs handling 1M+ requests/day",
                        "Developed React frontend"
                    ],
                    "technologies": ["JavaScript", "React", "Node.js"]
                }
            }
        ]
    
    @pytest.fixture
    def suitability_assessment(self):
        """Create sample suitability assessment."""
        return {
            "technical_fit_score": 82,
            "cultural_fit_score": 88,
            "key_strengths": [
                "Deep Python expertise with cloud architecture",
                "Proven team leadership and mentorship",
                "Strong API design and optimization skills"
            ],
            "critical_gaps": [
                "Limited experience with specific ML frameworks"
            ],
            "unique_value_proposition": "Rare combination of low-level optimization skills with high-level architecture vision. Can both design distributed systems and optimize their performance.",
            "overall_recommendation": "Strong candidate with excellent technical and cultural fit"
        }
    
    @pytest.fixture
    def shared_store(self, prioritized_experiences, suitability_assessment):
        """Create shared store with required data."""
        return {
            "prioritized_experiences": prioritized_experiences,
            "suitability_assessment": suitability_assessment,
            "requirements": {
                "required_skills": ["Python", "AWS", "Microservices"],
                "preferred_skills": ["Kubernetes", "ML", "Leadership"]
            },
            "job_title": "Senior Platform Engineer",
            "company_name": "InnovateTech"
        }
    
    @pytest.fixture
    def mock_narrative_response(self):
        """Mock LLM response for narrative strategy."""
        return {
            "must_tell_experiences": [
                {
                    "title": "Senior Software Engineer at TechCorp",
                    "reason": "Directly demonstrates platform engineering and team leadership",
                    "key_points": [
                        "Led microservices platform delivery with 5 engineers",
                        "40% latency reduction shows optimization expertise"
                    ]
                },
                {
                    "title": "ML Pipeline Automation Project",
                    "reason": "Shows innovation and automation mindset crucial for platform role",
                    "key_points": [
                        "Automated complex ML workflows reducing deployment time",
                        "Demonstrates Kubernetes expertise at scale"
                    ]
                }
            ],
            "differentiators": [
                "Combines platform architecture with performance optimization - rare skill",
                "ML automation experience brings AI-readiness to platform engineering"
            ],
            "career_arc": {
                "past": "Started as full-stack developer, discovered passion for backend optimization",
                "present": "Leading platform initiatives that enable entire engineering teams",
                "future": "Ready to architect next-generation platforms at InnovateTech"
            },
            "key_messages": [
                "Platform engineering expertise with proven team leadership",
                "Optimization mindset that delivers measurable business impact",
                "Ready to scale InnovateTech's infrastructure for growth"
            ],
            "evidence_stories": [
                {
                    "title": "Microservices Platform Transformation",
                    "challenge": "TechCorp's monolithic architecture was limiting team velocity and causing frequent outages. With 50+ developers blocked, we needed a complete platform overhaul within 6 months.",
                    "action": "Led a team of 5 engineers to design and implement a microservices platform. Established API standards, implemented service mesh with Istio, created CI/CD pipelines, and mentored teams on migration strategies.",
                    "result": "Delivered platform 2 weeks early. Reduced deployment time from days to 30 minutes, eliminated 90% of outages, and enabled 3x faster feature delivery. Platform now serves 100+ microservices.",
                    "skills_demonstrated": ["Platform Architecture", "Team Leadership", "Technical Mentorship"]
                }
            ]
        }
    
    def test_node_initialization(self, node):
        """Test node is initialized with correct settings."""
        assert node.max_retries == 2
        assert node.wait == 1
        assert hasattr(node, 'llm')
    
    def test_prep_validates_required_data(self, node):
        """Test prep validates required data is present."""
        # Missing prioritized experiences
        with pytest.raises(ValueError, match="No prioritized experiences"):
            node.prep({"suitability_assessment": {}})
        
        # Missing suitability assessment
        with pytest.raises(ValueError, match="No suitability assessment"):
            node.prep({"prioritized_experiences": [{"title": "Test"}]})
    
    def test_prep_extracts_context(self, node, shared_store):
        """Test prep extracts all required context."""
        context = node.prep(shared_store)
        
        assert "prioritized_experiences" in context
        assert "suitability_assessment" in context
        assert "requirements" in context
        assert context["job_title"] == "Senior Platform Engineer"
        assert context["company_name"] == "InnovateTech"
    
    def test_exec_generates_narrative_strategy(self, node, shared_store, mock_narrative_response):
        """Test exec generates complete narrative strategy."""
        context = node.prep(shared_store)
        
        # Mock LLM response
        node.llm.call_llm_structured_sync.return_value = mock_narrative_response
        
        result = node.exec(context)
        
        # Verify LLM was called
        node.llm.call_llm_structured_sync.assert_called_once()
        call_args = node.llm.call_llm_structured_sync.call_args
        assert call_args.kwargs["yaml_format"] is True
        assert call_args.kwargs["model"] == "claude-3-opus"
        
        # Verify result structure
        assert "must_tell_experiences" in result
        assert "differentiators" in result
        assert "career_arc" in result
        assert "key_messages" in result
        assert "evidence_stories" in result
    
    def test_prompt_includes_key_context(self, node, shared_store):
        """Test prompt includes all key context elements."""
        context = node.prep(shared_store)
        prompt = node._build_narrative_prompt(context)
        
        # Check key elements are in prompt
        assert "Senior Platform Engineer at InnovateTech" in prompt
        assert "Technical Fit: 82/100" in prompt
        assert "Cultural Fit: 88/100" in prompt
        assert "Senior Software Engineer" in prompt  # Top experience
        assert "Score: 85.5" in prompt  # Experience score
        assert "expert career coach" in prompt
        assert "CAR format" in prompt
    
    def test_experience_selection_logic(self, node, shared_store, mock_narrative_response):
        """Test that must-tell experiences are properly selected."""
        context = node.prep(shared_store)
        node.llm.call_llm_structured_sync.return_value = mock_narrative_response
        
        result = node.exec(context)
        
        must_tells = result["must_tell_experiences"]
        assert len(must_tells) >= 2
        assert len(must_tells) <= 3
        
        # Should include top-ranked experiences
        assert any("Senior Software Engineer" in exp["title"] for exp in must_tells)
    
    def test_differentiator_identification(self, node, shared_store, mock_narrative_response):
        """Test identification of unique differentiators."""
        context = node.prep(shared_store)
        node.llm.call_llm_structured_sync.return_value = mock_narrative_response
        
        result = node.exec(context)
        
        differentiators = result["differentiators"]
        assert len(differentiators) >= 1
        assert len(differentiators) <= 2
        assert any("rare" in diff.lower() or "unique" in diff.lower() for diff in differentiators)
    
    def test_career_arc_structure(self, node, shared_store, mock_narrative_response):
        """Test career arc has past, present, future structure."""
        context = node.prep(shared_store)
        node.llm.call_llm_structured_sync.return_value = mock_narrative_response
        
        result = node.exec(context)
        
        career_arc = result["career_arc"]
        assert "past" in career_arc
        assert "present" in career_arc
        assert "future" in career_arc
        assert "InnovateTech" in career_arc["future"]  # Should mention target company
    
    def test_key_messages_generation(self, node, shared_store, mock_narrative_response):
        """Test generation of key messages."""
        context = node.prep(shared_store)
        node.llm.call_llm_structured_sync.return_value = mock_narrative_response
        
        result = node.exec(context)
        
        key_messages = result["key_messages"]
        assert len(key_messages) == 3  # Should have exactly 3
        assert all(isinstance(msg, str) for msg in key_messages)
        assert all(len(msg) > 10 for msg in key_messages)  # Non-trivial messages
    
    def test_car_story_format(self, node, shared_store, mock_narrative_response):
        """Test evidence stories follow CAR format."""
        context = node.prep(shared_store)
        node.llm.call_llm_structured_sync.return_value = mock_narrative_response
        
        result = node.exec(context)
        
        stories = result["evidence_stories"]
        assert len(stories) >= 1
        assert len(stories) <= 2
        
        for story in stories:
            assert "title" in story
            assert "challenge" in story
            assert "action" in story
            assert "result" in story
            assert "skills_demonstrated" in story
            
            # Verify content is substantial
            assert len(story["challenge"]) > 50
            assert len(story["action"]) > 50
            assert len(story["result"]) > 50
    
    def test_fallback_strategy_on_error(self, node, shared_store):
        """Test fallback strategy is created on LLM error."""
        context = node.prep(shared_store)
        
        # Mock LLM to raise error
        node.llm.call_llm_structured_sync.side_effect = Exception("LLM error")
        
        result = node.exec(context)
        
        # Should return fallback strategy
        assert "must_tell_experiences" in result
        assert len(result["must_tell_experiences"]) == 3  # Top 3
        assert "differentiators" in result
        assert "career_arc" in result
        assert "key_messages" in result
        assert result["evidence_stories"] == []  # Empty in fallback
    
    def test_missing_fields_are_filled(self, node, shared_store):
        """Test missing fields in LLM response are filled with defaults."""
        context = node.prep(shared_store)
        
        # Mock incomplete LLM response
        incomplete_response = {
            "must_tell_experiences": [{"title": "Test", "reason": "Test"}],
            "career_arc": {"past": "Past", "present": "Present", "future": "Future"}
            # Missing: differentiators, key_messages, evidence_stories
        }
        node.llm.call_llm_structured_sync.return_value = incomplete_response
        
        result = node.exec(context)
        
        # Should have all required fields
        assert "differentiators" in result
        assert "key_messages" in result
        assert "evidence_stories" in result
        
        # Check defaults are reasonable
        assert len(result["differentiators"]) >= 2
        assert len(result["key_messages"]) == 3
        assert isinstance(result["evidence_stories"], list)
    
    def test_post_saves_to_shared_store(self, node, shared_store, mock_narrative_response):
        """Test post saves narrative strategy to shared store."""
        context = node.prep(shared_store)
        
        # Clear any existing strategy
        if "narrative_strategy" in shared_store:
            del shared_store["narrative_strategy"]
        
        action = node.post(shared_store, context, mock_narrative_response)
        
        assert action == "narrative"
        assert "narrative_strategy" in shared_store
        assert shared_store["narrative_strategy"] == mock_narrative_response
    
    def test_experience_summarization(self, node):
        """Test experience data summarization for prompt."""
        exp_data = {
            "role": "Senior Engineer",
            "company": "TechCorp",
            "achievements": ["Led team to deliver platform", "Improved performance"],
            "technologies": ["Python", "AWS", "Docker", "Kubernetes", "React"]
        }
        
        summary = node._summarize_experience_data(exp_data)
        
        assert "TechCorp" in summary
        assert "Led team to deliver platform" in summary  # First achievement
        assert "Python, AWS, Docker" in summary  # First 3 technologies
        assert "React" not in summary  # Beyond first 3
    
    def test_top_experiences_formatting(self, node, prioritized_experiences):
        """Test formatting of top experiences for prompt."""
        top_exps = [
            {
                "title": "Senior Engineer",
                "score": 85.5,
                "relevance": 90,
                "impact": 80,
                "summary": "Test summary"
            }
        ]
        
        formatted = node._format_top_experiences(top_exps)
        
        assert "1. Senior Engineer" in formatted
        assert "Score: 85.5" in formatted
        assert "Relevance: 90%" in formatted
        assert "Impact: 80%" in formatted
        assert "Test summary" in formatted
    
    def test_handles_empty_suitability_assessment(self, node, shared_store):
        """Test handling of minimal suitability assessment."""
        shared_store["suitability_assessment"] = {"minimal": True}  # Minimal but not empty
        
        context = node.prep(shared_store)
        prompt = node._build_narrative_prompt(context)
        
        # Should handle missing fields gracefully
        assert "Technical Fit: N/A/100" in prompt
        assert "Cultural Fit: N/A/100" in prompt
        assert "Key Strengths:" in prompt
        assert "Unique Value: N/A" in prompt
    
    def test_handles_many_experiences(self, node, shared_store):
        """Test handling of many prioritized experiences."""
        # Add 10 more experiences
        for i in range(10):
            shared_store["prioritized_experiences"].append({
                "rank": i + 4,
                "title": f"Experience {i+4}",
                "composite_score": 50 - i,
                "scores": {"relevance": 50, "recency": 50, "impact": 50, "uniqueness": 50, "growth": 50},
                "data": {"role": f"Role {i+4}"}
            })
        
        context = node.prep(shared_store)
        prompt = node._build_narrative_prompt(context)
        
        # Should only include top 5 in prompt
        assert "Experience 6" not in prompt  # 7th experience shouldn't be in prompt
        assert "1." in prompt
        assert "5." in prompt
        assert "6." not in prompt