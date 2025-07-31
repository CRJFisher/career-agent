"""
Unit tests for RequirementExtractionFlow.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from flow import RequirementExtractionFlow


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
Software Engineer - Backend Systems
    
We are looking for a talented backend engineer to join our team.
    
Requirements:
- Bachelor's degree in Computer Science
- 3+ years of experience with Python
- Experience with REST APIs and microservices
- Strong problem-solving skills
    
Nice to have:
- Experience with Kubernetes
- Open source contributions
    
Responsibilities:
- Design and implement scalable backend services
- Collaborate with frontend team
- Participate in code reviews
    
Benefits:
- Competitive salary
- Health insurance
- Remote work options
"""


class TestRequirementExtractionFlow:
    """Test RequirementExtractionFlow functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_flow_execution(self, sample_job_description):
        """Test successful flow execution."""
        with patch('flow.ExtractRequirementsNode') as mock_node_class:
            # Create mock node
            mock_node = Mock()
            mock_node.name = "ExtractRequirements"
            mock_node.execute = AsyncMock(return_value={
                'extraction_status': 'success',
                'job_requirements_structured': {
                    'role_summary': {
                        'title': 'Software Engineer',
                        'company': 'Unknown',
                        'location': 'Unknown',
                        'type': 'Full-time',
                        'level': 'Mid'
                    },
                    'hard_requirements': {
                        'education': ["Bachelor's degree in Computer Science"],
                        'experience': {
                            'years_required': 3,
                            'specific_experience': ["3+ years of experience with Python"]
                        }
                    },
                    'responsibilities': {
                        'primary': ["Design and implement scalable backend services"]
                    }
                }
            })
            mock_node_class.return_value = mock_node
            
            # Create and run flow
            flow = RequirementExtractionFlow()
            result = await flow.run(sample_job_description)
            
            # Verify results
            assert result['status'] == 'success'
            assert result['requirements'] is not None
            assert result['requirements']['role_summary']['title'] == 'Software Engineer'
            
            # Verify node was executed with correct store
            mock_node.execute.assert_called_once()
            call_args = mock_node.execute.call_args[0][0]
            assert call_args['job_description'] == sample_job_description
    
    @pytest.mark.asyncio
    async def test_extraction_failure(self, sample_job_description):
        """Test flow handling of extraction failure."""
        with patch('flow.ExtractRequirementsNode') as mock_node_class:
            # Create mock node that fails
            mock_node = Mock()
            mock_node.name = "ExtractRequirements"
            mock_node.execute = AsyncMock(return_value={
                'extraction_status': 'failed',
                'job_requirements_structured': None,
                'extraction_error': 'Invalid job description format'
            })
            mock_node_class.return_value = mock_node
            
            # Create and run flow
            flow = RequirementExtractionFlow()
            result = await flow.run(sample_job_description)
            
            # Verify failure handling
            assert result['status'] == 'failed'
            assert result['error'] == 'Invalid job description format'
            assert 'store' in result
    
    @pytest.mark.asyncio
    async def test_flow_execution_error(self, sample_job_description):
        """Test flow handling of execution errors."""
        with patch('flow.ExtractRequirementsNode') as mock_node_class:
            # Create mock node that raises exception
            mock_node = Mock()
            mock_node.name = "ExtractRequirements"
            mock_node.execute = AsyncMock(side_effect=Exception("Node execution failed"))
            mock_node_class.return_value = mock_node
            
            # Create and run flow
            flow = RequirementExtractionFlow()
            result = await flow.run(sample_job_description)
            
            # Verify error handling
            assert result['status'] == 'error'
            assert 'Node execution failed' in result['error']
            assert 'store' in result
    
    def test_flow_initialization(self):
        """Test flow is properly initialized."""
        with patch('flow.ExtractRequirementsNode') as mock_node_class:
            mock_node = Mock()
            mock_node.name = "ExtractRequirements"
            mock_node_class.return_value = mock_node
            
            flow = RequirementExtractionFlow()
            
            # Verify flow setup
            assert flow.name == "RequirementExtraction"
            assert "ExtractRequirements" in flow.nodes
            assert flow.nodes["ExtractRequirements"] == mock_node
    
    @pytest.mark.asyncio
    async def test_store_initialization(self, sample_job_description):
        """Test that store is properly initialized with job description."""
        with patch('flow.ExtractRequirementsNode') as mock_node_class:
            # Track store contents when execute is called
            store_contents = {}
            
            async def capture_store(store):
                store_contents.update(store)
                return {'extraction_status': 'success', 'job_requirements_structured': {}}
            
            mock_node = Mock()
            mock_node.name = "ExtractRequirements"
            mock_node.execute = AsyncMock(side_effect=capture_store)
            mock_node_class.return_value = mock_node
            
            # Create and run flow
            flow = RequirementExtractionFlow()
            await flow.run(sample_job_description)
            
            # Verify job description was in store
            assert 'job_description' in store_contents
            assert store_contents['job_description'] == sample_job_description