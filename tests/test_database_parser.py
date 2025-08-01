"""
Unit tests for career database parser utility.
"""

import pytest
import yaml
from pathlib import Path
import tempfile
import shutil
from utils.database_parser import (
    load_career_database,
    validate_career_database,
    merge_career_databases,
    CareerDatabaseError,
    CareerDatabaseParser
)


@pytest.fixture
def sample_career_data():
    """Sample career database data for testing with enhanced schema."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-234-567-8900",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe"
        },
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "duration": "2020-2023",
                "location": "San Francisco, CA",
                "description": "Led development of microservices architecture",
                "achievements": [
                    "Reduced latency by 50%", 
                    "Mentored 5 engineers",
                    "Led migration to Kubernetes"
                ],
                "technologies": ["Python", "Kubernetes", "AWS"],
                "team_size": 12,
                "reason_for_leaving": "Seeking new challenges",
                "company_culture_pros": ["Innovation-focused", "Great work-life balance"],
                "company_culture_cons": ["Rapid changes in priorities"],
                "projects": [
                    {
                        "title": "Payment Processing System",
                        "description": "Designed and implemented high-throughput payment processing system using event-driven architecture",
                        "achievements": [
                            "Processed $10M+ transactions daily",
                            "Achieved 99.99% uptime",
                            "Reduced processing time by 60%"
                        ],
                        "role": "Tech Lead",
                        "technologies": ["Python", "Kafka", "PostgreSQL"],
                        "key_stakeholders": ["CFO", "Payment Partners", "Compliance Team"],
                        "notable_challenges": [
                            "Implementing PCI compliance",
                            "Handling peak holiday traffic"
                        ],
                        "direct_reports": 3,
                        "reports_to": "Engineering Manager"
                    }
                ]
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "University of Technology",
                "year": "2016",
                "location": "Boston, MA",
                "gpa": "3.8/4.0",
                "honors": "Magna Cum Laude",
                "coursework": ["Machine Learning", "Distributed Systems", "Algorithms"]
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "Docker", "Kubernetes"],
            "soft": ["Leadership", "Communication", "Problem Solving"],
            "languages": ["English", "Spanish"],
            "tools": ["Git", "Jira", "VS Code"],
            "frameworks": ["Django", "React", "FastAPI"],
            "methodologies": ["Agile", "Scrum", "TDD"]
        },
        "projects": [
            {
                "name": "OpenSourceContrib",
                "type": "open_source",
                "description": "Major contributor to popular Python web framework",
                "role": "Core Contributor",
                "duration": "2019-Present",
                "technologies": ["Python", "GitHub Actions", "Docker"],
                "outcomes": [
                    "Implemented async support",
                    "500+ GitHub stars on my PRs",
                    "Improved performance by 30%"
                ],
                "url": "https://github.com/example/project",
                "context": "Started contributing to give back to the community",
                "team_size": 20,
                "users": "10K+ developers worldwide"
            }
        ],
        "certifications": [
            {
                "name": "AWS Solutions Architect",
                "issuer": "Amazon Web Services",
                "year": "2022",
                "credential_id": "AWS-123456",
                "url": "https://aws.amazon.com/verification/123456"
            }
        ]
    }


@pytest.fixture
def minimal_career_data():
    """Minimal valid career database."""
    return {
        "personal_info": {
            "name": "Jane Smith",
            "email": "jane@example.com"
        },
        "experience": [],
        "education": [],
        "skills": {
            "technical": ["Python"]
        }
    }


@pytest.fixture
def temp_yaml_file(tmp_path, sample_career_data):
    """Create a temporary YAML file with sample data."""
    yaml_file = tmp_path / "career.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(sample_career_data, f)
    return yaml_file


@pytest.fixture
def temp_yaml_dir(tmp_path, sample_career_data):
    """Create a temporary directory with multiple YAML files."""
    # Split data into multiple files
    personal_file = tmp_path / "01_personal.yaml"
    with open(personal_file, 'w') as f:
        yaml.dump({"personal_info": sample_career_data["personal_info"]}, f)
    
    experience_file = tmp_path / "02_experience.yaml"
    with open(experience_file, 'w') as f:
        yaml.dump({
            "experience": sample_career_data["experience"],
            "education": sample_career_data["education"]
        }, f)
    
    skills_file = tmp_path / "03_skills.yml"
    with open(skills_file, 'w') as f:
        yaml.dump({"skills": sample_career_data["skills"]}, f)
    
    projects_file = tmp_path / "04_projects.yaml"
    with open(projects_file, 'w') as f:
        yaml.dump({
            "projects": sample_career_data.get("projects", []),
            "certifications": sample_career_data.get("certifications", [])
        }, f)
    
    return tmp_path


class TestLoadCareerDatabase:
    """Test load_career_database function."""
    
    def test_load_single_file(self, temp_yaml_file, sample_career_data):
        """Test loading a single YAML file."""
        data = load_career_database(temp_yaml_file)
        assert data == sample_career_data
    
    def test_load_directory(self, temp_yaml_dir, sample_career_data):
        """Test loading directory of YAML files."""
        data = load_career_database(temp_yaml_dir)
        assert data["personal_info"] == sample_career_data["personal_info"]
        assert data["experience"] == sample_career_data["experience"]
        assert data["skills"] == sample_career_data["skills"]
        assert data["projects"] == sample_career_data["projects"]
    
    def test_file_not_found(self):
        """Test error handling for non-existent file."""
        with pytest.raises(CareerDatabaseError, match="Path does not exist"):
            load_career_database("nonexistent.yaml")
    
    def test_invalid_yaml(self, tmp_path):
        """Test error handling for invalid YAML."""
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content:")
        
        with pytest.raises(CareerDatabaseError, match="Invalid YAML format"):
            load_career_database(invalid_file)
    
    def test_non_yaml_file(self, tmp_path):
        """Test error handling for non-YAML file."""
        txt_file = tmp_path / "data.txt"
        txt_file.write_text("Not a YAML file")
        
        with pytest.raises(CareerDatabaseError, match="must have .yaml or .yml extension"):
            load_career_database(txt_file)
    
    def test_empty_directory(self, tmp_path):
        """Test error handling for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(CareerDatabaseError, match="No YAML files found"):
            load_career_database(empty_dir)
    
    def test_non_dict_yaml(self, tmp_path):
        """Test error handling for YAML that doesn't contain a dict."""
        list_file = tmp_path / "list.yaml"
        with open(list_file, 'w') as f:
            yaml.dump(["item1", "item2"], f)
        
        with pytest.raises(CareerDatabaseError, match="must contain a dictionary"):
            load_career_database(list_file)


class TestValidateCareerDatabase:
    """Test validate_career_database function."""
    
    def test_valid_database(self, sample_career_data):
        """Test validation of valid database."""
        warnings = validate_career_database(sample_career_data)
        assert len(warnings) == 0
    
    def test_minimal_valid_database(self, minimal_career_data):
        """Test validation of minimal valid database."""
        warnings = validate_career_database(minimal_career_data)
        assert len(warnings) == 0
    
    def test_missing_recommended_keys(self):
        """Test warnings for missing recommended keys."""
        data = {"some_other_key": "value"}
        warnings = validate_career_database(data)
        
        assert any("personal_info" in w for w in warnings)
        assert any("experience" in w for w in warnings)
        assert any("education" in w for w in warnings)
        assert any("skills" in w for w in warnings)
    
    def test_invalid_personal_info(self):
        """Test warnings for invalid personal_info structure."""
        data = {"personal_info": "not a dict"}
        warnings = validate_career_database(data)
        assert any("should be a dictionary" in w for w in warnings)
    
    def test_missing_personal_fields(self):
        """Test warnings for missing personal_info fields."""
        data = {"personal_info": {"phone": "123-456-7890"}}
        warnings = validate_career_database(data)
        assert any("name" in w for w in warnings)
        assert any("email" in w for w in warnings)
    
    def test_invalid_experience_format(self):
        """Test warnings for invalid experience format."""
        data = {"experience": "not a list"}
        warnings = validate_career_database(data)
        assert any("should be a list" in w for w in warnings)
    
    def test_invalid_experience_entry(self):
        """Test warnings for invalid experience entries."""
        data = {"experience": [{"description": "Some job"}]}
        warnings = validate_career_database(data)
        assert any("missing 'title' or 'company'" in w for w in warnings)
    
    def test_invalid_experience_projects(self):
        """Test warnings for invalid projects in experience."""
        data = {
            "experience": [{
                "title": "Engineer",
                "company": "Corp",
                "projects": "not a list"
            }]
        }
        warnings = validate_career_database(data)
        assert any("'projects' should be a list" in w for w in warnings)
    
    def test_invalid_project_entry(self):
        """Test warnings for invalid project entries in experience."""
        data = {
            "experience": [{
                "title": "Engineer",
                "company": "Corp",
                "projects": [{"title": "Project"}]  # Missing required fields
            }]
        }
        warnings = validate_career_database(data)
        assert any("missing required fields" in w for w in warnings)
    
    def test_invalid_standalone_projects(self):
        """Test warnings for invalid standalone projects."""
        data = {
            "projects": [{
                "name": "MyProject",
                "type": "invalid_type",  # Invalid project type
                "description": "Test",
                "technologies": ["Python"],
                "outcomes": ["Success"]
            }]
        }
        warnings = validate_career_database(data)
        assert any("invalid type" in w for w in warnings)


class TestMergeCareerDatabases:
    """Test merge_career_databases function."""
    
    def test_merge_non_conflicting(self):
        """Test merging databases with no conflicts."""
        db1 = {"personal_info": {"name": "John"}}
        db2 = {"skills": {"technical": ["Python"]}}
        
        merged = merge_career_databases(db1, db2)
        assert merged["personal_info"]["name"] == "John"
        assert merged["skills"]["technical"] == ["Python"]
    
    def test_merge_override(self):
        """Test that later databases override earlier ones."""
        db1 = {"personal_info": {"name": "John", "email": "old@example.com"}}
        db2 = {"personal_info": {"email": "new@example.com"}}
        
        merged = merge_career_databases(db1, db2)
        assert merged["personal_info"]["email"] == "new@example.com"
    
    def test_merge_lists(self):
        """Test that lists are concatenated."""
        db1 = {"experience": [{"title": "Job 1"}]}
        db2 = {"experience": [{"title": "Job 2"}]}
        
        merged = merge_career_databases(db1, db2)
        assert len(merged["experience"]) == 2
        assert merged["experience"][0]["title"] == "Job 1"
        assert merged["experience"][1]["title"] == "Job 2"
    
    def test_merge_multiple(self):
        """Test merging more than two databases."""
        db1 = {"a": 1}
        db2 = {"b": 2}
        db3 = {"c": 3, "a": 4}
        
        merged = merge_career_databases(db1, db2, db3)
        assert merged["a"] == 4  # Overridden by db3
        assert merged["b"] == 2
        assert merged["c"] == 3


class TestCareerDatabaseParser:
    """Test CareerDatabaseParser class."""
    
    def test_parse_valid_file(self, temp_yaml_file, sample_career_data):
        """Test parsing a valid career database file."""
        parser = CareerDatabaseParser()
        data = parser.parse(temp_yaml_file)
        
        assert data == sample_career_data
        assert len(parser.warnings) == 0
    
    def test_get_experience_projects(self, temp_yaml_file):
        """Test extracting projects from experience entries."""
        parser = CareerDatabaseParser()
        parser.parse(temp_yaml_file)
        
        projects = parser.get_experience_projects()
        assert len(projects) == 1
        assert projects[0]["title"] == "Payment Processing System"
        assert projects[0]["company"] == "Tech Corp"
        assert projects[0]["job_title"] == "Senior Software Engineer"
    
    def test_get_all_technologies(self, temp_yaml_file):
        """Test extracting all unique technologies."""
        parser = CareerDatabaseParser()
        parser.parse(temp_yaml_file)
        
        technologies = parser.get_all_technologies()
        
        # Should include technologies from skills, experience, and projects
        assert "Python" in technologies
        assert "Kubernetes" in technologies
        assert "Docker" in technologies
        assert "Kafka" in technologies  # From nested project
        assert "GitHub Actions" in technologies  # From standalone project
        
        # Should be sorted
        assert technologies == sorted(technologies)
    
    def test_get_achievements_by_role(self, temp_yaml_file):
        """Test extracting achievements by role."""
        parser = CareerDatabaseParser()
        parser.parse(temp_yaml_file)
        
        achievements = parser.get_achievements_by_role("Senior Software Engineer")
        
        # Should include achievements from both experience and nested projects
        assert "Reduced latency by 50%" in achievements
        assert "Processed $10M+ transactions daily" in achievements
        assert len(achievements) == 6  # 3 from experience + 3 from project
    
    def test_empty_data_methods(self):
        """Test parser methods with empty data."""
        parser = CareerDatabaseParser()
        
        assert parser.get_experience_projects() == []
        assert parser.get_all_technologies() == []
        assert parser.get_achievements_by_role("any") == []