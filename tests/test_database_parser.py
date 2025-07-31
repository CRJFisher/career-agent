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
    CareerDatabaseError
)


@pytest.fixture
def sample_career_data():
    """Sample career database data for testing."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-234-567-8900",
            "location": "San Francisco, CA"
        },
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "duration": "2020-2023",
                "description": "Led development of microservices",
                "achievements": ["Reduced latency by 50%", "Mentored 5 engineers"],
                "technologies": ["Python", "Kubernetes", "AWS"]
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "University of Technology",
                "year": "2016",
                "details": "GPA 3.8/4.0"
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "Docker"],
            "soft": ["Leadership", "Communication"],
            "languages": ["English", "Spanish"]
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