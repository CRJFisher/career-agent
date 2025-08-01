"""
Tests for RequirementMappingNode.

Tests the RAG-based requirement mapping functionality including:
- Keyword matching across career database
- Evidence retrieval from experience and projects
- Coverage score calculation
- Error handling
"""

import pytest
from unittest.mock import Mock, patch
from nodes import RequirementMappingNode


class TestRequirementMappingNode:
    """Test suite for RequirementMappingNode."""
    
    @pytest.fixture
    def node(self):
        """Create a RequirementMappingNode instance."""
        with patch('nodes.get_default_llm_wrapper') as mock_get_llm:
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            return RequirementMappingNode()
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample job requirements."""
        return {
            "required_skills": ["Python", "Docker", "Kubernetes"],
            "preferred_skills": ["Terraform", "AWS"],
            "experience_years": 5,
            "education": "Bachelor's degree in Computer Science",
            "responsibilities": {
                "primary": "Design scalable systems",
                "secondary": "Mentor junior developers"
            }
        }
    
    @pytest.fixture
    def sample_career_db(self):
        """Sample career database with experience and projects."""
        return {
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "description": "Led backend development using Python and Docker",
                    "achievements": [
                        "Migrated services to Kubernetes",
                        "Improved deployment pipeline"
                    ],
                    "technologies": ["Python", "Docker", "Kubernetes", "PostgreSQL"],
                    "projects": [
                        {
                            "title": "Microservices Migration",
                            "description": "Migrated monolith to microservices on Kubernetes",
                            "achievements": ["Reduced deployment time by 70%"],
                            "technologies": ["Kubernetes", "Helm", "Docker"]
                        }
                    ]
                },
                {
                    "title": "Software Developer",
                    "company": "StartupXYZ",
                    "description": "Full-stack development with Python and JavaScript",
                    "achievements": ["Built RESTful APIs"],
                    "technologies": ["Python", "React", "MongoDB"]
                }
            ],
            "projects": [
                {
                    "name": "Open Source Terraform Module",
                    "description": "Created Terraform modules for AWS infrastructure",
                    "outcomes": ["1000+ downloads", "20+ contributors"],
                    "technologies": ["Terraform", "AWS", "Python"]
                }
            ],
            "skills": {
                "programming": ["Python", "JavaScript", "Go"],
                "tools": ["Docker", "Kubernetes", "Git"],
                "cloud": ["AWS", "GCP"]
            }
        }
    
    def test_prep_success(self, node, sample_requirements, sample_career_db):
        """Test successful prep with valid data."""
        shared = {
            "requirements": sample_requirements,
            "career_database": sample_career_db
        }
        
        result = node.prep(shared)
        assert isinstance(result, tuple)
        assert result[0] == sample_requirements
        assert result[1] == sample_career_db
    
    def test_prep_missing_requirements(self, node):
        """Test prep with missing requirements."""
        shared = {"career_database": {}}
        
        with pytest.raises(ValueError, match="No requirements found"):
            node.prep(shared)
    
    def test_prep_missing_career_db(self, node, sample_requirements):
        """Test prep with missing career database."""
        shared = {"requirements": sample_requirements}
        
        with pytest.raises(ValueError, match="No career database found"):
            node.prep(shared)
    
    def test_exec_maps_exact_skills(self, node, sample_requirements, sample_career_db):
        """Test exact skill matching."""
        result = node.exec((sample_requirements, sample_career_db))
        
        # Check that Python, Docker, Kubernetes were found
        mapping = result["requirement_mapping_raw"]
        assert "required_skills" in mapping
        assert "Python" in mapping["required_skills"]
        assert "Docker" in mapping["required_skills"]
        assert "Kubernetes" in mapping["required_skills"]
        
        # Verify evidence was found
        python_evidence = mapping["required_skills"]["Python"]
        assert len(python_evidence) > 0
        assert any(e["match_type"] == "exact" for e in python_evidence)
    
    def test_exec_maps_partial_matches(self, node, sample_career_db):
        """Test partial matching functionality."""
        requirements = {
            "required_skills": ["Python programming", "Docker containers"]
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        
        # Should find evidence for Python programming (partial match with Python)
        assert "required_skills" in mapping
        assert "Python programming" in mapping["required_skills"]
        evidence = mapping["required_skills"]["Python programming"]
        assert len(evidence) > 0
        assert any(e["match_type"] == "partial" for e in evidence)
    
    def test_exec_searches_nested_projects(self, node, sample_career_db):
        """Test that nested projects within experience are searched."""
        requirements = {
            "required_skills": ["Helm"]  # Only in nested project
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        
        # Should find Helm in the nested project
        assert "required_skills" in mapping
        assert "Helm" in mapping["required_skills"]
        evidence = mapping["required_skills"]["Helm"]
        assert len(evidence) > 0
        assert evidence[0]["type"] == "experience_project"
        assert evidence[0]["title"] == "Microservices Migration"
    
    def test_exec_searches_standalone_projects(self, node, sample_career_db):
        """Test that standalone projects are searched."""
        requirements = {
            "preferred_skills": ["Terraform"]  # In standalone project
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        
        # Should find Terraform in standalone project
        assert "preferred_skills" in mapping
        assert "Terraform" in mapping["preferred_skills"]
        evidence = mapping["preferred_skills"]["Terraform"]
        assert len(evidence) > 0
        assert any(e["type"] == "project" for e in evidence)
    
    def test_exec_calculates_coverage_score(self, node, sample_requirements, sample_career_db):
        """Test coverage score calculation."""
        result = node.exec((sample_requirements, sample_career_db))
        
        assert "coverage_score" in result
        assert 0.0 <= result["coverage_score"] <= 1.0
        assert result["total_requirements"] > 0
        assert result["mapped_requirements"] <= result["total_requirements"]
    
    def test_exec_handles_dict_requirements(self, node, sample_career_db):
        """Test handling of dict-type requirements."""
        requirements = {
            "responsibilities": {
                "primary": "Python development",
                "secondary": "team mentoring"
            }
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        
        assert "responsibilities" in mapping
        assert "primary" in mapping["responsibilities"]
        # Should find evidence for Python development
        assert len(mapping["responsibilities"]["primary"]) > 0
    
    def test_exec_handles_single_value_requirements(self, node, sample_career_db):
        """Test handling of single value requirements."""
        requirements = {
            "education": "Python",  # Something that exists in the sample DB
            "team_size": "junior developers"  # Something that partially matches
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        
        # Should find evidence for Python
        assert "education" in mapping
        assert len(mapping["education"]) > 0
    
    def test_exec_limits_evidence_results(self, node, sample_career_db):
        """Test that evidence results are limited to top 5."""
        requirements = {
            "required_skills": ["Python"]  # Common skill with many matches
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        
        evidence = mapping["required_skills"]["Python"]
        assert len(evidence) <= 5  # Should be limited to 5 results
    
    def test_exec_sorts_by_match_quality(self, node, sample_career_db):
        """Test that exact matches come before partial matches."""
        # Create a requirement that will have both exact and partial matches
        requirements = {
            "required_skills": ["Python"]
        }
        
        result = node.exec((requirements, sample_career_db))
        mapping = result["requirement_mapping_raw"]
        evidence = mapping["required_skills"]["Python"]
        
        # If there are multiple matches, exact should come first
        if len(evidence) > 1:
            exact_indices = [i for i, e in enumerate(evidence) if e["match_type"] == "exact"]
            partial_indices = [i for i, e in enumerate(evidence) if e["match_type"] == "partial"]
            
            if exact_indices and partial_indices:
                assert max(exact_indices) < min(partial_indices)
    
    def test_post_stores_results(self, node, sample_requirements, sample_career_db):
        """Test that post stores results correctly."""
        shared = {}
        prep_res = (sample_requirements, sample_career_db)
        exec_res = {
            "requirement_mapping_raw": {"test": "mapping"},
            "coverage_score": 0.75,
            "total_requirements": 10,
            "mapped_requirements": 7
        }
        
        result = node.post(shared, prep_res, exec_res)
        
        assert shared["requirement_mapping_raw"] == {"test": "mapping"}
        assert shared["coverage_score"] == 0.75
        assert result == "default"
    
    def test_extract_searchable_content_empty_db(self, node):
        """Test extraction from empty career database."""
        content = node._extract_searchable_content({})
        assert content == []
    
    def test_extract_searchable_content_missing_sections(self, node):
        """Test extraction when some sections are missing."""
        career_db = {
            "experience": [
                {
                    "title": "Developer",
                    "company": "Tech Inc"
                }
            ]
            # Missing projects and skills sections
        }
        
        content = node._extract_searchable_content(career_db)
        assert len(content) == 1
        assert content[0]["type"] == "experience"
    
    def test_search_for_evidence_no_matches(self, node):
        """Test search when no matches are found."""
        searchable_content = [
            {
                "type": "experience",
                "title": "Developer",
                "text": "JavaScript React Node.js",
                "source": {}
            }
        ]
        
        evidence = node._search_for_evidence("Python Django", searchable_content)
        assert evidence == []
    
    def test_search_for_evidence_case_insensitive(self, node):
        """Test that search is case-insensitive."""
        searchable_content = [
            {
                "type": "skills",
                "title": "Skills",
                "text": "PYTHON docker KUBERNETES",
                "source": {}
            }
        ]
        
        evidence = node._search_for_evidence("python", searchable_content)
        assert len(evidence) > 0
        assert evidence[0]["match_type"] == "exact"
    
    def test_count_requirements_various_types(self, node):
        """Test counting requirements of various types."""
        requirements = {
            "skills": ["Python", "Docker", "K8s"],  # 3
            "experience": 5,  # 1
            "responsibilities": {  # 2
                "primary": "Design",
                "secondary": "Mentor"
            }
        }
        
        count = node._count_requirements(requirements)
        assert count == 6
    
    def test_count_mapped_requirements(self, node):
        """Test counting successfully mapped requirements."""
        mapping = {
            "skills": {
                "Python": [{"evidence": "found"}],  # 1
                "Docker": [{"evidence": "found"}],  # 1
                "K8s": []  # 0 - empty list
            },
            "experience": [{"evidence": "found"}],  # 1
            "education": None  # 0 - None value
        }
        
        count = node._count_mapped_requirements(mapping)
        assert count == 3  # Only non-empty values count
    
    def test_llm_initialization(self, node):
        """Test that LLM wrapper is initialized."""
        assert node.llm is not None
    
    def test_node_retry_configuration(self, node):
        """Test that node is configured with appropriate retries."""
        assert node.max_retries == 2
        assert node.wait == 1