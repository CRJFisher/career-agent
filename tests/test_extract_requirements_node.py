"""
Unit tests for ExtractRequirementsNode.
"""

import pytest
import asyncio
from nodes import ExtractRequirementsNode
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
Senior Software Engineer - Machine Learning Infrastructure

About the Role:
We are seeking an experienced Senior Software Engineer to join our ML Infrastructure team 
at TechCorp in San Francisco. This is a full-time position focused on building scalable 
systems for training and deploying machine learning models.

Requirements:
- Bachelor's degree in Computer Science or related field (Master's preferred)
- 5+ years of software engineering experience
- 3+ years working with distributed systems and cloud infrastructure
- Strong proficiency in Python, Go, or Java
- Experience with Kubernetes, Docker, and cloud platforms (AWS/GCP)
- Familiarity with ML frameworks like TensorFlow or PyTorch

Nice to Have:
- Experience with MLOps practices
- Contributions to open source projects
- Published papers or patents

Responsibilities:
- Design and implement scalable ML training pipelines
- Optimize model serving infrastructure for low latency
- Collaborate with data scientists and researchers
- Mentor junior engineers and lead technical projects
- Participate in on-call rotation

We Offer:
- Competitive salary ($180k-$250k)
- Stock options
- Comprehensive health insurance
- Learning and development budget
- Flexible work arrangements
"""


@pytest.fixture
def expected_requirements_structure():
    """Expected structure after extraction."""
    return {
        'role_summary': {
            'title': 'Senior Software Engineer',
            'company': 'TechCorp',
            'location': 'San Francisco',
            'type': 'Full-time',
            'level': 'Senior'
        },
        'hard_requirements': {
            'education': [
                "Bachelor's degree in Computer Science or related field",
                "Master's preferred"
            ],
            'experience': {
                'years_required': 5,
                'specific_experience': [
                    "5+ years of software engineering experience",
                    "3+ years working with distributed systems and cloud infrastructure"
                ]
            },
            'technical_skills': {
                'programming_languages': ['Python', 'Go', 'Java'],
                'technologies': ['Kubernetes', 'Docker', 'AWS/GCP'],
                'concepts': ['Distributed systems', 'Machine learning']
            }
        },
        'nice_to_have': {
            'experience': [
                "Experience with MLOps practices",
                "Contributions to open source projects"
            ],
            'skills': ["Published papers or patents"]
        },
        'responsibilities': {
            'primary': [
                "Design and implement scalable ML training pipelines",
                "Optimize model serving infrastructure for low latency",
                "Collaborate with data scientists and researchers",
                "Mentor junior engineers and lead technical projects"
            ],
            'secondary': ["Participate in on-call rotation"]
        },
        'compensation_benefits': {
            'salary_range': "$180k-$250k",
            'benefits': [
                "Stock options",
                "Comprehensive health insurance",
                "Learning and development budget"
            ],
            'perks': ["Flexible work arrangements"]
        }
    }


class TestExtractRequirementsNode:
    """Test ExtractRequirementsNode functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_extraction(self, sample_job_description):
        """Test successful requirements extraction."""
        # Mock the LLM wrapper
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            # Create mock LLM that returns structured data
            mock_llm = Mock()
            mock_llm.call_llm_structured = AsyncMock(return_value={
                'role_summary': {
                    'title': 'Senior Software Engineer',
                    'company': 'TechCorp',
                    'location': 'San Francisco'
                },
                'hard_requirements': {
                    'education': ["Bachelor's degree in Computer Science"],
                    'experience': {'years_required': 5}
                },
                'responsibilities': {
                    'primary': ["Design ML infrastructure"]
                }
            })
            mock_get_llm.return_value = mock_llm
            
            # Create node and execute
            node = ExtractRequirementsNode()
            store = {'job_description': sample_job_description}
            
            result = await node.execute(store)
            
            # Verify results
            assert result['extraction_status'] == 'success'
            assert result['job_requirements_structured'] is not None
            assert 'role_summary' in result['job_requirements_structured']
            
            # Verify LLM was called correctly
            mock_llm.call_llm_structured.assert_called_once()
            call_args = mock_llm.call_llm_structured.call_args
            assert call_args.kwargs['output_format'] == 'yaml'
            assert call_args.kwargs['temperature'] == 0.3
    
    @pytest.mark.asyncio
    async def test_missing_job_description(self):
        """Test error handling when job description is missing."""
        node = ExtractRequirementsNode()
        store = {}  # Empty store
        
        with pytest.raises(ValueError, match="No job description found"):
            await node.execute(store)
    
    @pytest.mark.asyncio
    async def test_llm_error_handling(self, sample_job_description):
        """Test error handling when LLM fails."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            # Create mock LLM that raises an error
            mock_llm = Mock()
            mock_llm.call_llm_structured = AsyncMock(
                side_effect=Exception("LLM API error")
            )
            mock_get_llm.return_value = mock_llm
            
            node = ExtractRequirementsNode()
            store = {'job_description': sample_job_description}
            
            result = await node.execute(store)
            
            # Verify error handling
            assert result['extraction_status'] == 'failed'
            assert result['job_requirements_structured'] is None
            assert 'LLM API error' in result['extraction_error']
    
    @pytest.mark.asyncio
    async def test_validation_missing_sections(self, sample_job_description):
        """Test validation when required sections are missing."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            # Create mock LLM that returns incomplete data
            mock_llm = Mock()
            mock_llm.call_llm_structured = AsyncMock(return_value={
                'role_summary': {'title': 'Engineer'},
                # Missing hard_requirements and responsibilities
            })
            mock_get_llm.return_value = mock_llm
            
            node = ExtractRequirementsNode()
            store = {'job_description': sample_job_description}
            
            result = await node.execute(store)
            
            # Verify validation error
            assert result['extraction_status'] == 'failed'
            assert 'Missing required section' in result['extraction_error']
    
    def test_validate_requirements_success(self):
        """Test requirements validation with valid data."""
        node = ExtractRequirementsNode()
        
        valid_requirements = {
            'role_summary': {'title': 'Engineer'},
            'hard_requirements': {'education': ["Bachelor's"]},
            'responsibilities': {'primary': ["Build stuff"]}
        }
        
        # Should not raise exception
        node._validate_requirements(valid_requirements)
    
    def test_validate_requirements_missing_title(self):
        """Test validation error for missing title."""
        node = ExtractRequirementsNode()
        
        invalid_requirements = {
            'role_summary': {},  # Missing title
            'hard_requirements': {'education': ["Bachelor's"]},
            'responsibilities': {'primary': ["Build stuff"]}
        }
        
        with pytest.raises(ValueError, match="Missing job title"):
            node._validate_requirements(invalid_requirements)
    
    def test_create_extraction_prompt(self, sample_job_description):
        """Test prompt creation includes job description."""
        node = ExtractRequirementsNode()
        node.job_description = sample_job_description
        
        prompt = node._create_extraction_prompt()
        
        # Verify prompt contains key elements
        assert "Extract the job requirements" in prompt
        assert "YAML format" in prompt
        assert sample_job_description in prompt
        assert "role_summary:" in prompt  # Example format
        assert "hard_requirements:" in prompt  # Example format