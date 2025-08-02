"""
Tests for CVGenerationNode.

Tests CV generation based on narrative strategy and career database.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from nodes import CVGenerationNode


class TestCVGenerationNode:
    """Test suite for CVGenerationNode."""
    
    @pytest.fixture
    def node(self):
        """Create node instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return CVGenerationNode()
    
    @pytest.fixture
    def narrative_strategy(self):
        """Create sample narrative strategy."""
        return {
            "must_tell_experiences": [
                {
                    "title": "Senior Software Engineer at TechCorp",
                    "reason": "Directly demonstrates platform engineering",
                    "key_points": [
                        "Led team of 5 engineers on platform",
                        "Reduced latency by 40%"
                    ]
                },
                {
                    "title": "ML Pipeline Project",
                    "reason": "Shows automation expertise",
                    "key_points": [
                        "Automated deployment process",
                        "Built scalable infrastructure"
                    ]
                }
            ],
            "differentiators": [
                "Combines optimization with architecture skills"
            ],
            "career_arc": {
                "past": "Started as developer",
                "present": "Leading platform teams",
                "future": "Ready for InnovateTech"
            },
            "key_messages": [
                "Platform expertise",
                "Leadership experience",
                "Delivery track record"
            ],
            "evidence_stories": []
        }
    
    @pytest.fixture
    def career_db(self):
        """Create sample career database."""
        return {
            "personal_information": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "location": "San Francisco, CA"
            },
            "professional_experience": [
                {
                    "role": "Senior Software Engineer",
                    "company": "TechCorp",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "responsibilities": [
                        "Lead platform engineering team",
                        "Design microservices architecture",
                        "Mentor junior engineers"
                    ],
                    "achievements": [
                        "Reduced API latency by 40% through optimization",
                        "Led migration to Kubernetes serving 100+ services",
                        "Mentored 3 engineers to senior level"
                    ],
                    "technologies": ["Python", "AWS", "Kubernetes", "Docker"]
                },
                {
                    "role": "Software Engineer",
                    "company": "StartupXYZ",
                    "start_date": "2019-06",
                    "end_date": "2021-12",
                    "achievements": [
                        "Built REST APIs handling 1M+ requests/day"
                    ],
                    "technologies": ["JavaScript", "Node.js", "MongoDB"]
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "UC Berkeley",
                    "graduation_date": "2019"
                }
            ],
            "skills": {
                "Programming Languages": ["Python", "JavaScript", "Go"],
                "Cloud & Infrastructure": ["AWS", "Kubernetes", "Docker"],
                "Databases": ["PostgreSQL", "MongoDB", "Redis"]
            },
            "certifications": [
                {
                    "name": "AWS Solutions Architect",
                    "date": "2023"
                }
            ]
        }
    
    @pytest.fixture
    def requirements(self):
        """Create sample job requirements."""
        return {
            "required_skills": ["Python", "AWS", "Microservices"],
            "preferred_skills": ["Kubernetes", "Leadership"],
            "experience_years": {"min": 5, "max": 10},
            "education": ["Computer Science", "Engineering"]
        }
    
    @pytest.fixture
    def shared_store(self, narrative_strategy, career_db, requirements):
        """Create shared store with all required data."""
        return {
            "narrative_strategy": narrative_strategy,
            "career_db": career_db,
            "requirements": requirements,
            "job_title": "Senior Platform Engineer",
            "company_name": "InnovateTech"
        }
    
    def test_node_initialization(self, node):
        """Test node is initialized correctly."""
        assert node.max_retries == 2
        assert node.wait == 1
        assert hasattr(node, 'llm')
    
    def test_prep_validates_required_data(self, node):
        """Test prep validates required inputs."""
        # Empty narrative strategy
        with pytest.raises(ValueError, match="No narrative strategy"):
            node.prep({"narrative_strategy": {}, "career_db": {}})
        
        # Missing career database
        with pytest.raises(ValueError, match="No career database"):
            node.prep({"narrative_strategy": {"key_messages": ["test"]}, "career_db": {}})
    
    def test_prep_extracts_context(self, node, shared_store):
        """Test prep extracts all required context."""
        context = node.prep(shared_store)
        
        assert "narrative_strategy" in context
        assert "career_db" in context
        assert "requirements" in context
        assert context["job_title"] == "Senior Platform Engineer"
        assert context["company_name"] == "InnovateTech"
    
    def test_exec_generates_cv(self, node, shared_store):
        """Test exec generates CV markdown."""
        context = node.prep(shared_store)
        
        # Mock LLM response
        mock_cv = """# John Doe
john.doe@email.com | San Francisco, CA

## Professional Summary
Platform engineering expert with proven leadership experience and consistent delivery track record.

## Professional Experience

### Senior Software Engineer | TechCorp | 2022-01 - Present
Leading platform engineering initiatives
- Reduced API latency by 40% through systematic optimization
- Led migration to Kubernetes serving 100+ microservices
- Mentored 3 junior engineers to senior level

### Software Engineer | StartupXYZ | 2019-06 - 2021-12
- Built REST APIs handling 1M+ requests/day

## Education
### BS Computer Science | UC Berkeley | 2019

## Technical Skills
- **Programming Languages**: Python, JavaScript, Go
- **Cloud & Infrastructure**: AWS, Kubernetes, Docker
"""
        
        node.llm.call_llm_sync.return_value = mock_cv
        
        result = node.exec(context)
        
        # Verify LLM was called
        node.llm.call_llm_sync.assert_called_once()
        call_args = node.llm.call_llm_sync.call_args
        assert "max_tokens" in call_args.kwargs
        
        # Verify result
        assert "John Doe" in result
        assert "Professional Summary" in result
        assert "Platform engineering expert" in result
    
    def test_prompt_includes_narrative_elements(self, node, shared_store):
        """Test prompt includes all narrative strategy elements."""
        context = node.prep(shared_store)
        prompt = node._build_cv_prompt(context)
        
        # Check narrative elements
        assert "Platform expertise" in prompt  # Key message
        assert "Leadership experience" in prompt  # Key message
        assert "Senior Software Engineer at TechCorp" in prompt  # Must-tell
        assert "Combines optimization with architecture" in prompt  # Differentiator
        assert "Ready for InnovateTech" in prompt  # Career arc future
    
    def test_prompt_includes_requirements(self, node, shared_store):
        """Test prompt includes job requirements."""
        context = node.prep(shared_store)
        prompt = node._build_cv_prompt(context)
        
        # Check requirements
        assert "Python, AWS, Microservices" in prompt  # Required skills
        assert "Kubernetes, Leadership" in prompt  # Preferred skills
        assert "5-10 years" in prompt  # Experience range
    
    def test_prompt_includes_career_data(self, node, shared_store):
        """Test prompt includes career database info."""
        context = node.prep(shared_store)
        prompt = node._build_cv_prompt(context)
        
        # Check career data
        assert "John Doe" in prompt
        assert "john.doe@email.com" in prompt
        assert "[MUST-TELL] Senior Software Engineer at TechCorp" in prompt
        assert "Reduced API latency by 40%" in prompt
        assert "AWS Solutions Architect" in prompt
    
    def test_must_tell_prioritization(self, node, shared_store):
        """Test must-tell experiences are marked in prompt."""
        context = node.prep(shared_store)
        career_text = node._format_career_db_for_cv(
            context["career_db"],
            ["Senior Software Engineer at TechCorp"]
        )
        
        # Must-tell should be marked
        assert "[MUST-TELL]" in career_text
        assert "[MUST-TELL] Senior Software Engineer at TechCorp" in career_text
        
        # Non-must-tell should not be marked
        assert "[MUST-TELL] Software Engineer at StartupXYZ" not in career_text
    
    def test_fallback_cv_generation(self, node, shared_store):
        """Test fallback CV when generation fails."""
        context = node.prep(shared_store)
        
        # Mock LLM failure
        node.llm.call_llm_sync.side_effect = Exception("LLM error")
        
        result = node.exec(context)
        
        # Should return fallback
        assert "# John Doe" in result
        assert "john.doe@email.com | San Francisco, CA" in result
        assert "## Professional Summary" in result
        assert "Platform expertise" in result  # Key message
        assert "Senior Software Engineer | TechCorp" in result
    
    def test_short_cv_triggers_fallback(self, node, shared_store):
        """Test short CV triggers fallback."""
        context = node.prep(shared_store)
        
        # Mock very short response
        node.llm.call_llm_sync.return_value = "Too short"
        
        result = node.exec(context)
        
        # Should use fallback
        assert len(result) > 500
        assert "# John Doe" in result
    
    def test_post_stores_cv(self, node, shared_store):
        """Test post stores CV in shared store."""
        cv_markdown = """# John Doe

## Professional Summary
Test summary

## Professional Experience
### Senior Engineer | Company | 2022 - Present
- Achievement 1

## Education
### BS Computer Science | University | 2019
"""
        
        # Clear any existing CV
        if "cv_markdown" in shared_store:
            del shared_store["cv_markdown"]
        
        action = node.post(shared_store, {}, cv_markdown)
        
        assert action == "cv_generated"
        assert "cv_markdown" in shared_store
        assert shared_store["cv_markdown"] == cv_markdown
    
    def test_post_logging(self, node, shared_store):
        """Test post logs CV summary."""
        cv_markdown = """# John Doe

## Professional Summary
Summary here

## Core Skills
Skills here

## Professional Experience
Experience here

## Education
Education here
"""
        
        with patch('nodes.logger') as mock_logger:
            node.post(shared_store, {}, cv_markdown)
            
            # Should log line count (14 lines including empty lines)
            mock_logger.info.assert_any_call("Generated CV with 14 lines")
            
            # Should log section count
            mock_logger.info.assert_any_call("CV sections: 4")
            
            # Should log section names
            calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Professional Summary" in call for call in calls)
    
    def test_format_requirements(self, node):
        """Test requirements formatting."""
        requirements = {
            "required_skills": ["Python", "AWS"],
            "preferred_skills": ["Docker"],
            "experience_years": {"min": 3, "max": 5},
            "education": ["Computer Science"]
        }
        
        formatted = node._format_requirements(requirements)
        
        assert "Required Skills: Python, AWS" in formatted
        assert "Preferred Skills: Docker" in formatted
        assert "Experience: 3-5 years" in formatted
        assert "Education: Computer Science" in formatted
    
    def test_format_requirements_edge_cases(self, node):
        """Test requirements formatting edge cases."""
        # Single year experience
        req1 = {"experience_years": 5}
        formatted1 = node._format_requirements(req1)
        assert "Experience: 5 years" in formatted1
        
        # No requirements
        req2 = {}
        formatted2 = node._format_requirements(req2)
        assert formatted2 == "No specific requirements provided"
    
    def test_markdown_formatting(self, node, shared_store):
        """Test CV uses proper markdown formatting."""
        context = node.prep(shared_store)
        prompt = node._build_cv_prompt(context)
        
        # Check markdown format is requested
        assert "GitHub-flavored Markdown" in prompt
        assert "```markdown" in prompt
        assert "# [Full Name]" in prompt
        assert "## Professional Summary" in prompt
        assert "### [Job Title]" in prompt
        assert "- [Achievement" in prompt
    
    def test_handles_missing_personal_info(self, node, shared_store):
        """Test handling of missing personal information."""
        # Remove personal info
        del shared_store["career_db"]["personal_information"]
        
        context = node.prep(shared_store)
        
        # Should not fail
        fallback_cv = node._create_fallback_cv(context)
        assert "# Professional" in fallback_cv
        assert "email@example.com" in fallback_cv
    
    def test_handles_empty_sections(self, node, shared_store):
        """Test handling of empty career database sections."""
        # Empty skills
        shared_store["career_db"]["skills"] = {}
        
        # Empty certifications
        shared_store["career_db"]["certifications"] = []
        
        context = node.prep(shared_store)
        career_text = node._format_career_db_for_cv(
            context["career_db"],
            []
        )
        
        # Should handle gracefully
        assert "SKILLS:" not in career_text  # Empty section skipped
        assert "CERTIFICATIONS:" not in career_text  # Empty section skipped
        assert "PROFESSIONAL EXPERIENCE:" in career_text  # Non-empty section included
    
    def test_experience_year_formatting(self, node):
        """Test various experience year formats."""
        # Dict format
        req1 = {"experience_years": {"min": 5, "max": 10}}
        formatted1 = node._format_requirements(req1)
        assert "Experience: 5-10 years" in formatted1
        
        # Dict with no max
        req2 = {"experience_years": {"min": 5}}
        formatted2 = node._format_requirements(req2)
        assert "Experience: 5-N/A years" in formatted2
    
    def test_project_experiences_included(self, node, shared_store):
        """Test that project experiences are handled."""
        # Add project to career db
        shared_store["career_db"]["projects"] = [
            {
                "name": "ML Pipeline Project",
                "description": "Automated ML deployment",
                "technologies": ["Python", "Kubernetes"],
                "date": "2023"
            }
        ]
        
        # Add to must-tell
        shared_store["narrative_strategy"]["must_tell_experiences"].append({
            "title": "ML Pipeline Project",
            "reason": "Shows automation",
            "key_points": ["Automated deployment"]
        })
        
        context = node.prep(shared_store)
        prompt = node._build_cv_prompt(context)
        
        # Project should be in must-tell list
        assert "ML Pipeline Project" in prompt