"""Unit tests for BuildDatabaseNode."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import yaml
from datetime import datetime

from nodes import BuildDatabaseNode


class TestBuildDatabaseNode:
    """Test suite for BuildDatabaseNode."""
    
    @pytest.fixture
    def node(self):
        """Create node instance."""
        return BuildDatabaseNode()
    
    @pytest.fixture
    def sample_extractions(self):
        """Sample extracted experiences from multiple documents."""
        return [
            {
                "document_name": "resume.pdf",
                "extraction_confidence": 0.9,
                "personal_info": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "123-456-7890"
                },
                "experiences": [
                    {
                        "company": "Tech Corp",
                        "title": "Senior Engineer",
                        "duration": "2020-Present",
                        "description": "Led engineering team",
                        "achievements": ["Reduced latency by 40%"],
                        "technologies": ["Python", "AWS"],
                        "projects": [
                            {
                                "title": "API Redesign",
                                "description": "Complete API overhaul",
                                "achievements": ["Improved performance by 50%"],
                                "technologies": ["Python", "FastAPI"]
                            }
                        ]
                    }
                ],
                "education": [
                    {
                        "degree": "BS Computer Science",
                        "institution": "Tech University",
                        "year": "2016"
                    }
                ],
                "skills": {
                    "technical": ["Python", "JavaScript", "AWS"],
                    "tools": ["Docker", "Git"]
                }
            },
            {
                "document_name": "portfolio.md",
                "extraction_confidence": 0.8,
                "personal_info": {
                    "name": "John Doe",
                    "linkedin": "https://linkedin.com/in/johndoe"
                },
                "experiences": [
                    {
                        "company": "Tech Corp, Inc.",  # Duplicate with suffix
                        "title": "Sr. Engineer",  # Variation of Senior Engineer
                        "duration": "Jan 2020 - Present",
                        "description": "Engineering leadership role",
                        "achievements": ["Reduced latency by 40%", "Mentored 5 junior engineers"],
                        "technologies": ["Python", "PostgreSQL"],
                        "projects": []
                    }
                ],
                "projects": [
                    {
                        "name": "Open Source Tool",
                        "type": "open_source",
                        "description": "CLI tool for developers",
                        "technologies": ["Go", "Docker"],
                        "outcomes": ["1000+ GitHub stars"]
                    }
                ]
            }
        ]
    
    def test_prep_default_values(self, node):
        """Test prep method with default values."""
        shared = {}
        
        result = node.prep(shared)
        
        assert result["extracted_experiences"] == []
        assert result["existing_database"] is None
        assert result["output_path"] == "career_database.yaml"
        assert result["merge_strategy"] == "smart"
    
    def test_prep_with_custom_values(self, node, sample_extractions):
        """Test prep method with custom values."""
        existing_db = {"personal_info": {"name": "Jane Doe"}}
        shared = {
            "extracted_experiences": sample_extractions,
            "existing_career_database": existing_db,
            "database_output_path": "output/career.yaml",
            "merge_strategy": "replace"
        }
        
        result = node.prep(shared)
        
        assert result["extracted_experiences"] == sample_extractions
        assert result["existing_database"] == existing_db
        assert result["output_path"] == "output/career.yaml"
        assert result["merge_strategy"] == "replace"
    
    def test_aggregate_extractions(self, node, sample_extractions):
        """Test aggregation of extracted data."""
        result = node._aggregate_extractions(sample_extractions)
        
        # Check personal info aggregation (should prefer longer values)
        assert result["personal_info"]["name"] == "John Doe"
        assert result["personal_info"]["email"] == "john@example.com"
        assert result["personal_info"]["linkedin"] == "https://linkedin.com/in/johndoe"
        
        # Check experiences collected
        assert len(result["experiences"]) == 2
        
        # Check skills aggregation (should be combined)
        assert "Python" in result["skills"]["technical"]
        assert "JavaScript" in result["skills"]["technical"]
        assert "Docker" in result["skills"]["tools"]
        
        # Check projects collected
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "Open Source Tool"
    
    def test_deduplicate_experiences(self, node):
        """Test experience deduplication."""
        experiences = [
            {
                "company": "Tech Corp",
                "title": "Senior Engineer",
                "duration": "2020-Present",
                "achievements": ["Achievement 1"],
                "technologies": ["Python"]
            },
            {
                "company": "Tech Corp, Inc.",  # Same company with suffix
                "title": "Sr. Engineer",  # Same role, different abbreviation
                "duration": "Jan 2020 - Present",
                "achievements": ["Achievement 1", "Achievement 2"],
                "technologies": ["Python", "AWS"]
            }
        ]
        
        result = node._deduplicate_experiences(experiences)
        
        # Should merge into one experience
        assert len(result) == 1
        assert result[0]["company"] in ["Tech Corp", "Tech Corp, Inc."]
        assert len(result[0]["achievements"]) == 2  # Combined unique achievements
        assert set(result[0]["technologies"]) == {"Python", "AWS"}
    
    def test_merge_experience_group(self, node):
        """Test merging of duplicate experiences."""
        experiences = [
            {
                "company": "Tech Corp",
                "title": "Engineer",
                "duration": "2020-2023",
                "description": "Short description",
                "achievements": ["Achievement 1"],
                "projects": [
                    {"title": "Project A", "description": "Description A", "achievements": ["Result 1"]}
                ]
            },
            {
                "company": "Tech Corp",
                "title": "Engineer",
                "duration": "Jan 2020 - Dec 2023",  # More specific
                "description": "Much longer and more detailed description",
                "achievements": ["Achievement 1", "Achievement 2"],
                "projects": [
                    {"title": "Project A", "description": "Description A", "achievements": ["Result 1", "Result 2"]},
                    {"title": "Project B", "description": "Description B", "achievements": ["Result 3"]}
                ]
            }
        ]
        
        result = node._merge_experience_group(experiences)
        
        # Should use most detailed as base
        assert "longer and more detailed" in result["description"]
        # Should use more specific duration
        assert result["duration"] == "Jan 2020 - Dec 2023"
        # Should merge achievements
        assert len(result["achievements"]) == 2
        # Should merge projects
        assert len(result["projects"]) == 2
        # Project A should have merged achievements
        project_a = next(p for p in result["projects"] if p["title"] == "Project A")
        assert len(project_a["achievements"]) == 2
    
    def test_build_database_structure(self, node):
        """Test building final database structure."""
        deduped_data = {
            "personal_info": {"name": "John Doe"},
            "experiences": [{"company": "Tech Corp", "title": "Engineer"}],
            "education": [{"degree": "BS CS", "institution": "University"}],
            "skills": {
                "technical": ["Python"],
                "soft": [],  # Empty should be filtered
                "tools": ["Git"]
            },
            "projects": [],  # Empty should be omitted
            "certifications": [{"name": "AWS Certified"}],
            "publications": [],  # Empty should be omitted
            "awards": []  # Empty should be omitted
        }
        
        result = node._build_database(deduped_data)
        
        # Required sections should always be present
        assert "personal_info" in result
        assert "experience" in result
        assert "education" in result
        assert "skills" in result
        
        # Empty skill categories should be filtered
        assert "technical" in result["skills"]
        assert "tools" in result["skills"]
        assert "soft" not in result["skills"]
        
        # Empty optional sections should be omitted
        assert "projects" not in result
        assert "publications" not in result
        assert "awards" not in result
        
        # Non-empty optional sections should be included
        assert "certifications" in result
    
    def test_normalize_company_name(self, node):
        """Test company name normalization."""
        assert node._normalize_company_name("Tech Corp") == "tech corp"
        assert node._normalize_company_name("Tech Corp, Inc.") == "tech corp"
        assert node._normalize_company_name("Tech Corp, LLC") == "tech corp"
        assert node._normalize_company_name("TECH CORP") == "tech corp"
    
    def test_normalize_job_title(self, node):
        """Test job title normalization."""
        assert node._normalize_job_title("Senior Engineer") == "senior engineer"
        assert node._normalize_job_title("Sr. Engineer") == "senior engineer"
        assert node._normalize_job_title("Software Engineer") == "engineer"
        assert node._normalize_job_title("Jr Software Developer") == "junior developer"
    
    def test_standardize_technologies(self, node):
        """Test technology name standardization."""
        tech_list = ["javascript", "PYTHON", "react.js", "nodejs", "aws", "k8s"]
        
        result = node._standardize_technologies(tech_list)
        
        assert result == ["JavaScript", "Python", "React", "Node.js", "AWS", "Kubernetes"]
    
    def test_parse_date_from_duration(self, node):
        """Test date parsing from duration strings."""
        # Year only
        date1 = node._parse_date_from_duration("2020-Present")
        assert date1.year == 2020
        
        # Month Year
        date2 = node._parse_date_from_duration("Jan 2020 - Dec 2023")
        assert date2.year == 2020
        assert date2.month == 1
        
        # Invalid format
        date3 = node._parse_date_from_duration("Current")
        assert date3 is None
    
    @patch('utils.database_parser.validate_with_schema')
    def test_exec_complete_flow(self, mock_validate, node, sample_extractions):
        """Test complete exec flow."""
        mock_validate.return_value = []  # No validation errors
        
        prep_res = {
            "extracted_experiences": sample_extractions,
            "existing_database": None,
            "merge_strategy": "smart"
        }
        
        result = node.exec(prep_res)
        
        # Check career database built
        assert "career_database" in result
        assert "personal_info" in result["career_database"]
        assert "experience" in result["career_database"]
        
        # Check deduplication worked
        assert len(result["career_database"]["experience"]) == 1  # Should merge duplicates
        
        # Check summary generated
        assert "summary" in result
        assert result["summary"]["total_documents_processed"] == 2
        assert result["summary"]["experiences_after_dedup"] == 1
        
        # Check validation
        assert result["validation_errors"] == []
    
    def test_merge_with_existing_smart(self, node):
        """Test smart merge with existing database."""
        new_db = {
            "personal_info": {"name": "John Doe"},
            "experience": [{"company": "New Corp", "title": "Engineer"}],
            "skills": {"technical": ["Python"]}
        }
        
        existing_db = {
            "personal_info": {"name": "John Doe", "email": "john@old.com"},
            "experience": [{"company": "Old Corp", "title": "Developer"}],
            "skills": {"technical": ["JavaScript"], "tools": ["Git"]}
        }
        
        result = node._merge_with_existing(new_db, existing_db, "smart")
        
        # Should preserve existing email since new doesn't have it
        assert result["personal_info"]["email"] == "john@old.com"
        
        # Should have both experiences
        assert len(result["experience"]) == 2
        
        # Should merge skills
        assert set(result["skills"]["technical"]) == {"Python", "JavaScript"}
        assert result["skills"]["tools"] == ["Git"]
    
    def test_generate_summary(self, node, sample_extractions):
        """Test summary generation."""
        career_db = {
            "personal_info": {"name": "John Doe", "email": "john@example.com"},
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "Engineer",
                    "duration": "2020-Present",
                    "projects": [{"title": "Project A"}, {"title": "Project B"}]
                }
            ],
            "skills": {"technical": ["Python", "JavaScript"]}
        }
        
        summary = node._generate_summary(career_db, sample_extractions, [])
        
        assert summary["total_documents_processed"] == 2
        assert summary["successful_extractions"] == 2
        assert summary["experiences_after_dedup"] == 1
        assert len(summary["companies"]) == 1
        assert summary["companies"][0]["name"] == "Tech Corp"
        assert summary["companies"][0]["projects"] == 2
        assert "Python" in summary["technologies_found"]
        assert summary["data_completeness"]["has_email"] is True
        assert summary["data_completeness"]["has_projects"] is True
    
    @patch('utils.database_parser.save_career_database')
    def test_post_saves_and_stores(self, mock_save, node):
        """Test post method saves database and updates shared."""
        shared = {}
        prep_res = {"output_path": "test_output.yaml"}
        exec_res = {
            "career_database": {"personal_info": {"name": "John"}},
            "summary": {
                "total_documents_processed": 5,
                "experiences_after_dedup": 3,
                "companies": [],
                "technologies_found": []
            },
            "validation_errors": []
        }
        
        action = node.post(shared, prep_res, exec_res)
        
        # Should save to file
        mock_save.assert_called_once_with(
            {"personal_info": {"name": "John"}},
            "test_output.yaml"
        )
        
        # Should update shared
        assert shared["career_database"] == exec_res["career_database"]
        assert shared["build_summary"] == exec_res["summary"]
        assert "validation_errors" not in shared  # No errors
        
        # Should return complete
        assert action == "complete"