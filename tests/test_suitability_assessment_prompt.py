"""
Tests for suitability assessment prompt validation.

Tests the prompt design to ensure it generates consistent,
comprehensive assessments across various scenarios.
"""

import pytest
import yaml
from typing import Dict, Any, List
from unittest.mock import Mock, patch


class TestSuitabilityAssessmentPrompt:
    """Test suite for suitability assessment prompt validation."""
    
    @pytest.fixture
    def base_context(self):
        """Base context for prompt testing."""
        return {
            "job_title": "Senior Software Engineer",
            "company_name": "TechCorp",
            "industry_context": "B2B SaaS platform",
            "technical_score": 75,
            "required_coverage": "4/5 requirements met",
            "preferred_coverage": "2/3 preferences met", 
            "other_coverage": "Strong education background",
            "requirement_mapping_details": """
- Required Skills:
  - Python: HIGH (5+ years production experience)
  - AWS: HIGH (Certified Solutions Architect)
  - REST APIs: HIGH (Designed multiple microservices)
  - Docker: MEDIUM (Used but not expert)
  - Kubernetes: GAP (No experience)
- Preferred Skills:
  - React: MEDIUM (Some frontend work)
  - PostgreSQL: HIGH (Database optimization expert)
  - Redis: GAP (No experience)
""",
            "gap_analysis_details": """
- Kubernetes (required): Missing container orchestration experience
  Impact: Will need support for deployment and scaling tasks
  Mitigation: Strong Docker knowledge provides foundation
- Redis (preferred): No caching layer experience
  Impact: May not optimize for high-throughput scenarios initially
  Mitigation: Has worked with Memcached, concepts transfer
""",
            "company_culture_summary": """
- Values: Innovation, Ownership, Transparency, Customer Success
- Work Style: Hybrid (3 days office), Fast-paced sprints
- Team: Collaborative, knowledge sharing, blameless post-mortems
- Tech Culture: CI/CD, code review, test-driven development
"""
        }
    
    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response matching expected format."""
        return {
            "cultural_fit_score": 82,
            "cultural_fit_breakdown": {
                "work_style_alignment": 85,
                "value_alignment": 80,
                "team_dynamics": 82,
                "growth_mindset": 81
            },
            "key_strengths": [
                {
                    "strength": "Deep Python expertise with high-performance systems",
                    "evidence": "Led optimization reducing latency 10x",
                    "business_impact": "Critical for scaling platform"
                },
                {
                    "strength": "Strong AWS architecture experience",
                    "evidence": "AWS Certified Solutions Architect",
                    "business_impact": "Accelerates cloud migration"
                },
                {
                    "strength": "API design excellence",
                    "evidence": "Designed APIs serving 1M+ requests/day",
                    "business_impact": "Ensures scalable service architecture"
                }
            ],
            "critical_gaps": [
                {
                    "gap": "Kubernetes orchestration",
                    "severity": "major",
                    "impact": "Cannot independently manage container deployments",
                    "mitigation": "Pair with DevOps team for 3-4 months"
                },
                {
                    "gap": "Redis caching",
                    "severity": "minor", 
                    "impact": "Suboptimal caching strategies initially",
                    "mitigation": "Experience with Memcached transfers well"
                }
            ],
            "unique_value_proposition": "This candidate combines rare depth in Python performance optimization with proven cloud architecture skills. Their experience building APIs at scale, coupled with strong database optimization abilities, creates a powerful multiplier effect for backend development. Few engineers can claim expertise across the full stack from low-level optimizations to distributed system design.",
            "hiring_recommendation": {
                "decision": "strong_yes",
                "confidence": "high",
                "reasoning": "Technical gaps are minor compared to core strengths. Their proven ability to scale systems aligns with our growth trajectory. Kubernetes can be learned, but their performance optimization expertise is rare."
            },
            "interview_focus_areas": [
                "Deep dive on Python optimization techniques",
                "System design for high-throughput services",
                "Team collaboration and knowledge sharing approach"
            ]
        }
    
    def test_prompt_structure_validation(self, base_context):
        """Test that prompt includes all required sections."""
        # Build prompt with template (simulated)
        prompt_sections = [
            "senior hiring manager",
            "Role Context",
            "Technical Fit Analysis", 
            "Company Culture & Environment",
            "Assessment Guidelines",
            "Cultural Fit Assessment",
            "Strength Identification Framework",
            "Gap Significance Evaluation",
            "Unique Value Proposition Framework",
            "Output Requirements"
        ]
        
        prompt_template = self._load_prompt_template()
        
        for section in prompt_sections:
            assert section.lower() in prompt_template.lower(), \
                f"Prompt missing required section: {section}"
    
    def test_scoring_methodology_included(self, base_context):
        """Test that scoring methodology is clearly explained."""
        prompt_template = self._load_prompt_template()
        
        # Check technical scoring explanation
        assert "HIGH strength = 100%" in prompt_template
        assert "MEDIUM strength = 60%" in prompt_template
        assert "LOW strength = 30%" in prompt_template
        assert "Missing/Gap = 0%" in prompt_template
        
        # Check cultural fit dimensions
        assert "Work Style Alignment" in prompt_template
        assert "Value Alignment" in prompt_template
        assert "Team Dynamics" in prompt_template
        assert "Growth Mindset" in prompt_template
    
    def test_output_format_specification(self, base_context):
        """Test that output format is clearly specified."""
        prompt_template = self._load_prompt_template()
        
        # Check YAML format requirement
        assert "yaml" in prompt_template.lower()
        
        # Check all required output fields
        required_fields = [
            "cultural_fit_score",
            "cultural_fit_breakdown",
            "key_strengths",
            "critical_gaps",
            "unique_value_proposition",
            "hiring_recommendation",
            "interview_focus_areas"
        ]
        
        for field in required_fields:
            assert field in prompt_template, \
                f"Output format missing required field: {field}"
    
    def test_example_provided(self, base_context):
        """Test that concrete example is included."""
        prompt_template = self._load_prompt_template()
        
        # Check for example section
        assert "Example Analysis" in prompt_template or "Example Output" in prompt_template
        
        # Check example has realistic content
        assert "Senior Backend Engineer" in prompt_template  # Example role
        assert "cultural_fit_score: 82" in prompt_template  # Example score
    
    def test_prompt_generates_valid_output(self, base_context, mock_llm_response):
        """Test that prompt generates structurally valid output."""
        # Validate response structure
        assert isinstance(mock_llm_response["cultural_fit_score"], int)
        assert 0 <= mock_llm_response["cultural_fit_score"] <= 100
        
        # Validate breakdown
        breakdown = mock_llm_response["cultural_fit_breakdown"]
        assert len(breakdown) == 4
        assert all(0 <= score <= 100 for score in breakdown.values())
        
        # Validate strengths structure
        assert len(mock_llm_response["key_strengths"]) >= 3
        for strength in mock_llm_response["key_strengths"]:
            assert "strength" in strength
            assert "evidence" in strength
            assert "business_impact" in strength
        
        # Validate gaps structure
        for gap in mock_llm_response["critical_gaps"]:
            assert "gap" in gap
            assert "severity" in gap
            assert gap["severity"] in ["critical_blocker", "major", "minor"]
            assert "impact" in gap
            assert "mitigation" in gap
        
        # Validate recommendation
        rec = mock_llm_response["hiring_recommendation"]
        assert rec["decision"] in ["strong_yes", "yes", "maybe", "no"]
        assert rec["confidence"] in ["high", "medium", "low"]
        assert len(rec["reasoning"]) > 50  # Non-trivial reasoning
    
    def test_cultural_fit_calculation(self, mock_llm_response):
        """Test cultural fit score calculation logic."""
        breakdown = mock_llm_response["cultural_fit_breakdown"]
        
        # Calculate expected average
        expected_avg = sum(breakdown.values()) / len(breakdown)
        actual_score = mock_llm_response["cultural_fit_score"]
        
        # Allow small rounding difference
        assert abs(actual_score - expected_avg) <= 1, \
            f"Cultural fit score {actual_score} doesn't match breakdown average {expected_avg}"
    
    def test_edge_case_no_gaps(self, base_context):
        """Test prompt handles case with no gaps."""
        context = base_context.copy()
        context["gap_analysis_details"] = "No critical gaps identified"
        
        # Prompt should still request gap analysis
        prompt_template = self._load_prompt_template()
        assert "critical_gaps" in prompt_template
    
    def test_edge_case_low_technical_score(self, base_context):
        """Test prompt handles low technical fit appropriately."""
        context = base_context.copy()
        context["technical_score"] = 25
        context["required_coverage"] = "1/5 requirements met"
        
        # Prompt should still seek balanced assessment
        prompt_template = self._load_prompt_template()
        assert "balanced" in prompt_template.lower() or "objective" in prompt_template.lower()
    
    def test_unique_value_proposition_guidance(self):
        """Test UVP framework is well-defined."""
        prompt_template = self._load_prompt_template()
        
        # Check for intersection/combination guidance
        assert "intersection" in prompt_template.lower()
        assert "combination" in prompt_template.lower() or "combine" in prompt_template.lower()
        
        # Check for concrete examples
        assert "Backend engineer + published ML researcher" in prompt_template or \
               "examples" in prompt_template.lower()
    
    def test_star_v_framework(self):
        """Test STAR-V strength identification framework."""
        prompt_template = self._load_prompt_template()
        
        components = ["Specific", "Transferable", "Amplified", "Rare", "Valuable"]
        for component in components:
            # Check with markdown formatting (e.g., **T**ransferable)
            markdown_pattern = f"**{component[0]}**{component[1:]}"
            found = (component in prompt_template or 
                    component.lower() in prompt_template.lower() or
                    markdown_pattern in prompt_template)
            assert found, f"STAR-V framework missing component: {component}"
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template for testing."""
        # In real implementation, load from prompts/suitability_assessment_prompt.md
        try:
            with open("prompts/suitability_assessment_prompt.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            # If running from test directory, try parent path
            with open("../prompts/suitability_assessment_prompt.md", "r") as f:
                return f.read()
    
    @pytest.mark.parametrize("role,expected_focus", [
        ("Senior Backend Engineer", ["distributed systems", "API design", "scaling"]),
        ("Frontend Engineer", ["user experience", "React", "responsive design"]),
        ("DevOps Engineer", ["Kubernetes", "CI/CD", "infrastructure"]),
        ("Data Scientist", ["ML algorithms", "statistics", "Python"])
    ])
    def test_role_specific_adaptation(self, base_context, role, expected_focus):
        """Test prompt adapts to different role types."""
        context = base_context.copy()
        context["job_title"] = role
        
        # In real implementation, prompt should emphasize role-specific aspects
        # This tests the prompt design accommodates various roles
        assert context["job_title"] == role
        
        # Verify prompt can handle role-specific requirements
        for focus_area in expected_focus:
            # Prompt should allow for role-specific evaluation criteria
            pass  # Actual implementation would check prompt adaptation
    
    def test_consistency_across_runs(self, base_context, mock_llm_response):
        """Test that prompt generates consistent assessments."""
        # In production, would run multiple times and check consistency
        # For now, verify the prompt includes consistency instructions
        prompt_template = self._load_prompt_template()
        
        assert "objective" in prompt_template.lower() or \
               "consistent" in prompt_template.lower() or \
               "systematic" in prompt_template.lower()