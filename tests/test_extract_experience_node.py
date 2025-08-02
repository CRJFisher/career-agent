"""Unit tests for ExtractExperienceNode."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import yaml

from nodes import ExtractExperienceNode
from utils.document_parser import ParsedDocument, DocumentSection


class TestExtractExperienceNode:
    """Test suite for ExtractExperienceNode."""
    
    @pytest.fixture
    def node(self):
        """Create node instance with mocked LLM."""
        with patch('nodes.get_default_llm_wrapper') as mock_llm:
            mock_llm.return_value = Mock()
            node = ExtractExperienceNode()
            return node
    
    @pytest.fixture
    def sample_documents(self):
        """Sample document sources."""
        return [
            {
                "path": "/path/to/resume.pdf",
                "name": "resume.pdf",
                "type": ".pdf",
                "size": 50000,
                "modified_date": "2024-01-15T10:30:00",
                "source": "local"
            },
            {
                "path": "/path/to/project.md",
                "name": "project.md",
                "type": ".md",
                "size": 10000,
                "modified_date": "2024-02-20T14:45:00",
                "source": "local"
            }
        ]
    
    @pytest.fixture
    def parsed_resume(self):
        """Sample parsed resume document."""
        return ParsedDocument(
            content="""John Doe
Software Engineer

Experience:
Senior Software Engineer at Tech Corp (2020-Present)
- Led team of 5 engineers
- Reduced API latency by 40%
- Technologies: Python, FastAPI, PostgreSQL

Projects:
- API Redesign: Complete overhaul of REST API
  - Improved performance by 50%
  - Technologies: Python, FastAPI

Education:
BS Computer Science, University of Tech (2016)
""",
            metadata={"pages": 2},
            sections=[
                DocumentSection("Experience", "...", 1),
                DocumentSection("Education", "...", 1)
            ],
            source_type="pdf",
            source_path="/path/to/resume.pdf"
        )
    
    def test_prep_with_documents(self, node, sample_documents):
        """Test prep method prepares documents correctly."""
        shared = {
            "document_sources": sample_documents,
            "extraction_mode": "targeted"
        }
        
        result = node.prep(shared)
        
        assert result["documents"] == sample_documents
        assert result["batch_size"] == 5
        assert result["extraction_mode"] == "targeted"
        assert "career_schema" in result
    
    def test_prep_with_custom_schema(self, node, sample_documents):
        """Test prep method uses custom schema when available."""
        custom_schema = {"custom": "schema"}
        shared = {
            "document_sources": sample_documents,
            "career_database_schema": custom_schema
        }
        
        result = node.prep(shared)
        
        assert result["career_schema"] == custom_schema
    
    def test_prep_defaults(self, node):
        """Test prep method with minimal shared data."""
        shared = {}
        
        result = node.prep(shared)
        
        assert result["documents"] == []
        assert result["batch_size"] == 5
        assert result["extraction_mode"] == "comprehensive"
        assert result["career_schema"] is not None
    
    @patch('utils.document_parser.parse_document')
    def test_exec_batch_success(self, mock_parse, node, sample_documents, parsed_resume):
        """Test successful batch execution."""
        # Setup mocks
        mock_parse.return_value = parsed_resume
        
        # Mock LLM response
        llm_response = yaml.dump({
            "personal_info": {"name": "John Doe", "email": "john@example.com"},
            "experience": [{
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "duration": "2020-Present",
                "description": "Led engineering team",
                "achievements": ["Reduced API latency by 40%"],
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
                "projects": [{
                    "title": "API Redesign",
                    "description": "Complete overhaul of REST API",
                    "achievements": ["Improved performance by 50%"],
                    "technologies": ["Python", "FastAPI"]
                }]
            }],
            "education": [{
                "degree": "BS Computer Science",
                "institution": "University of Tech",
                "year": "2016"
            }],
            "skills": {
                "technical": ["Python", "FastAPI", "PostgreSQL"]
            }
        })
        node.llm.complete.return_value = llm_response
        
        prep_res = {
            "career_schema": node._get_default_career_schema(),
            "extraction_mode": "comprehensive"
        }
        
        # Execute
        result = node.exec_batch([sample_documents[0]], prep_res)
        
        # Verify
        assert len(result) == 1
        extraction = result[0]
        assert extraction["document_name"] == "resume.pdf"
        assert extraction["extraction_confidence"] > 0.5
        assert len(extraction["experiences"]) == 1
        assert extraction["experiences"][0]["company"] == "Tech Corp"
        assert len(extraction["experiences"][0]["projects"]) == 1
    
    @patch('utils.document_parser.parse_document')
    def test_exec_batch_parse_error(self, mock_parse, node, sample_documents):
        """Test handling of document parsing errors."""
        # Mock parse error
        mock_parse.return_value = ParsedDocument(
            content="",
            error="Failed to parse PDF",
            source_path="/path/to/resume.pdf"
        )
        
        prep_res = {
            "career_schema": node._get_default_career_schema(),
            "extraction_mode": "comprehensive"
        }
        
        # Execute
        result = node.exec_batch([sample_documents[0]], prep_res)
        
        # Verify error handling
        assert len(result) == 1
        extraction = result[0]
        assert extraction["extraction_confidence"] == 0.0
        assert extraction["error"] == "Failed to parse PDF"
        assert extraction["experiences"] == []
    
    @patch('utils.document_parser.parse_document')
    def test_exec_batch_llm_yaml_error(self, mock_parse, node, sample_documents, parsed_resume):
        """Test handling of invalid YAML from LLM."""
        # Setup mocks
        mock_parse.return_value = parsed_resume
        
        # Mock invalid YAML response
        node.llm.complete.return_value = "Invalid YAML: {unclosed bracket"
        
        prep_res = {
            "career_schema": node._get_default_career_schema(),
            "extraction_mode": "comprehensive"
        }
        
        # Execute
        result = node.exec_batch([sample_documents[0]], prep_res)
        
        # Verify fallback extraction
        assert len(result) == 1
        extraction = result[0]
        assert extraction["extraction_confidence"] == 0.3
        assert "Failed to parse structured response" in extraction["error"]
        assert extraction["experiences"] == []
    
    def test_classify_document_resume(self, node, parsed_resume):
        """Test document classification for resumes."""
        doc_metadata = {"name": "john_resume.pdf"}
        
        doc_type = node._classify_document(parsed_resume, doc_metadata)
        
        assert doc_type == "resume"
    
    def test_classify_document_project(self, node):
        """Test document classification for project documents."""
        parsed_doc = ParsedDocument(
            content="Project Overview\n\nThis project implements...",
            sections=[
                DocumentSection("Overview", "...", 1),
                DocumentSection("Implementation", "...", 1)
            ],
            source_type="md"
        )
        doc_metadata = {"name": "api_project.md"}
        
        doc_type = node._classify_document(parsed_doc, doc_metadata)
        
        assert doc_type == "portfolio"  # 'project' in filename triggers portfolio classification
    
    def test_calculate_extraction_confidence_high(self, node):
        """Test confidence calculation for complete extraction."""
        extracted_data = {
            "personal_info": {"name": "John Doe"},
            "experiences": [{
                "company": "Tech Corp",
                "title": "Engineer",
                "duration": "2020-2023",
                "achievements": ["Improved performance by 40%"],
                "projects": [{"title": "API Project"}]
            }],
            "education": [{"degree": "BS CS"}],
            "skills": {"technical": ["Python"]},
            "projects": []
        }
        
        confidence = node._calculate_extraction_confidence(extracted_data)
        
        assert confidence > 0.7
    
    def test_calculate_extraction_confidence_low(self, node):
        """Test confidence calculation for incomplete extraction."""
        extracted_data = {
            "personal_info": {},
            "experiences": [],
            "education": [],
            "skills": {},
            "projects": []
        }
        
        confidence = node._calculate_extraction_confidence(extracted_data)
        
        assert confidence == 0.0
    
    def test_structure_extraction(self, node):
        """Test structuring of extracted data."""
        raw_extraction = {
            "personal_info": {"name": "John Doe"},
            "experience": [{
                "company": "Tech Corp",
                "title": "Engineer",
                "duration": "2020-2023",
                "achievements": ["Achievement 1"],
                "projects": [{
                    "title": "Project A",
                    "description": "Description",
                    "achievements": ["Result 1"]
                }]
            }],
            "skills": {"technical": ["Python"]}
        }
        doc_metadata = {"path": "/path", "name": "resume.pdf"}
        
        result = node._structure_extraction(raw_extraction, doc_metadata, "resume")
        
        assert result["document_source"] == "/path"
        assert result["document_name"] == "resume.pdf"
        assert result["document_type"] == "resume"
        assert len(result["experiences"]) == 1
        assert len(result["experiences"][0]["projects"]) == 1
        assert result["skills"]["technical"] == ["Python"]
    
    def test_post_stores_results(self, node):
        """Test post method stores extraction results."""
        shared = {}
        prep_res = {}
        
        # Mock extraction results
        exec_res = [
            [{
                "document_name": "doc1.pdf",
                "extraction_confidence": 0.9,
                "experiences": [{"company": "Company A"}]
            }],
            [{
                "document_name": "doc2.pdf",
                "extraction_confidence": 0.2,
                "error": "Parsing failed",
                "experiences": []
            }]
        ]
        
        action = node.post(shared, prep_res, exec_res)
        
        assert action == "continue"
        assert "extracted_experiences" in shared
        assert len(shared["extracted_experiences"]) == 2
        assert shared["extraction_summary"]["total_documents"] == 2
        assert shared["extraction_summary"]["successful_extractions"] == 1
        assert shared["extraction_summary"]["failed_extractions"] == 1
    
    def test_create_system_prompt(self, node):
        """Test system prompt generation."""
        schema = {"test": "schema"}
        
        prompt = node._create_system_prompt(schema, "resume", "comprehensive")
        
        assert "career analyst" in prompt
        assert "comprehensive" in prompt.lower()
        assert "extract every detail" in prompt.lower()
    
    def test_create_user_prompt(self, node, parsed_resume):
        """Test user prompt generation."""
        doc_metadata = {"name": "resume.pdf", "source": "local"}
        
        prompt = node._create_user_prompt(parsed_resume, doc_metadata, "resume")
        
        assert "resume.pdf" in prompt
        assert "John Doe" in prompt
        assert "Extract complete work history" in prompt
    
    def test_create_user_prompt_truncation(self, node):
        """Test user prompt truncates long documents."""
        # Create very long content
        long_content = "A" * 20000
        parsed_doc = ParsedDocument(content=long_content)
        doc_metadata = {"name": "long.pdf", "source": "local"}
        
        prompt = node._create_user_prompt(parsed_doc, doc_metadata, "general")
        
        assert len(prompt) < 20000
        assert "[Content truncated...]" in prompt