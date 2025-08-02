"""
Tests for company research validator.

Tests validation logic for company research YAML schema including:
- Required field validation
- Type checking
- Length constraints
- Enum validation
- Nested structure validation
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from utils.company_research_validator import CompanyResearchValidator


class TestCompanyResearchValidator:
    """Test suite for CompanyResearchValidator."""
    
    def test_minimal_valid_structure(self):
        """Test that minimal valid structure passes validation."""
        data = CompanyResearchValidator.create_minimal_valid()
        is_valid, errors = CompanyResearchValidator.validate(data)
        
        assert is_valid is True
        assert errors == []
    
    def test_complete_valid_structure(self):
        """Test complete structure with all optional fields."""
        data = {
            "mission": "To revolutionize healthcare through AI-powered diagnostics and personalized treatment plans",
            "team_scope": {
                "team_name": "ML Platform Team",
                "size": "15-20 engineers",
                "responsibilities": [
                    "Building ML infrastructure",
                    "Model deployment pipelines",
                    "Performance optimization"
                ],
                "reports_to": "VP of Engineering"
            },
            "strategic_importance": {
                "business_impact": "Critical for company's AI-first strategy, enabling rapid deployment of ML models across all products",
                "growth_trajectory": "Team doubling in size to support new product lines",
                "innovation_areas": ["AutoML", "Edge deployment", "Real-time inference"]
            },
            "culture": {
                "values": ["Innovation", "Impact", "Collaboration", "Learning"],
                "work_style": {
                    "remote_policy": "Remote-first",
                    "collaboration_style": "Async-first with weekly sync meetings",
                    "pace": "Fast-paced startup environment"
                },
                "employee_experience": {
                    "satisfaction_indicators": ["4.6/5 Glassdoor", "90% retention"],
                    "growth_opportunities": "Conference budget and 20% time for learning"
                }
            },
            "technology_stack_practices": {
                "languages": ["Python", "Go", "TypeScript"],
                "frameworks": ["TensorFlow", "FastAPI", "React"],
                "infrastructure": ["AWS", "Kubernetes", "Airflow"],
                "practices": ["CI/CD", "Code review", "A/B testing"]
            },
            "recent_developments": {
                "product_launches": [
                    {
                        "name": "AI Diagnostics v3",
                        "date": "2024-01-15",
                        "impact": "50% faster diagnoses"
                    }
                ],
                "organizational_changes": ["Series C funding", "New CTO"],
                "press_coverage": ["TechCrunch feature", "Forbes 30 Under 30"]
            },
            "market_position_growth": {
                "market_position": "Emerging leader in healthcare AI",
                "growth_metrics": {
                    "revenue_growth": "150% YoY",
                    "user_growth": "100k healthcare providers",
                    "funding_stage": "Series C ($100M)"
                },
                "competitive_advantages": ["FDA approvals", "Hospital partnerships"]
            }
        }
        
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is True
        assert errors == []
    
    def test_missing_required_fields(self):
        """Test detection of missing required fields."""
        data = {
            "mission": "A" * 50,
            "team_scope": {
                "team_name": "Team",
                "size": "10",
                "responsibilities": ["R1", "R2"]
            }
            # Missing: strategic_importance, culture
        }
        
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("Missing required fields" in error for error in errors)
        assert any("strategic_importance" in error for error in errors)
        assert any("culture" in error for error in errors)
    
    def test_missing_nested_required_fields(self):
        """Test detection of missing nested required fields."""
        data = CompanyResearchValidator.create_minimal_valid()
        # Remove required nested field
        del data["team_scope"]["responsibilities"]
        
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("team_scope" in error and "responsibilities" in error for error in errors)
    
    def test_type_validation(self):
        """Test type checking for fields."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # Wrong type for string field
        data["mission"] = 123
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("mission" in error and "should be str" in error for error in errors)
        
        # Reset and test wrong type for dict field
        data["mission"] = "A" * 50
        data["team_scope"] = "Not a dict"
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("team_scope" in error and "should be dict" in error for error in errors)
        
        # Reset and test wrong type for list field
        data["team_scope"] = {
            "team_name": "Team",
            "size": "10",
            "responsibilities": "Not a list"
        }
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("responsibilities" in error and "should be list" in error for error in errors)
    
    def test_string_length_validation(self):
        """Test string length constraints."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # Too short mission
        data["mission"] = "Too short"
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("mission" in error and "too short" in error for error in errors)
        
        # Too long mission
        data["mission"] = "A" * 501
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("mission" in error and "too long" in error for error in errors)
        
        # Too short business_impact
        data["mission"] = "A" * 50
        data["strategic_importance"]["business_impact"] = "Short"
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("business_impact" in error and "too short" in error for error in errors)
    
    def test_list_size_validation(self):
        """Test list size constraints."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # Too few responsibilities
        data["team_scope"]["responsibilities"] = ["Only one"]
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("responsibilities" in error and "too few" in error for error in errors)
        
        # Too many values
        data["team_scope"]["responsibilities"] = ["R1", "R2"]
        data["culture"]["values"] = ["V1", "V2", "V3", "V4", "V5", "V6", "V7"]
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("values" in error and "too many" in error for error in errors)
    
    def test_enum_validation(self):
        """Test enum value constraints."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # Invalid remote_policy
        data["culture"]["work_style"]["remote_policy"] = "Invalid-policy"
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("remote_policy" in error and "invalid value" in error for error in errors)
        
        # Valid remote_policy values
        for valid_policy in ["Remote-first", "Hybrid", "Office-first", "Flexible"]:
            data["culture"]["work_style"]["remote_policy"] = valid_policy
            is_valid, errors = CompanyResearchValidator.validate(data)
            assert is_valid is True
    
    def test_work_style_nested_validation(self):
        """Test special validation for work_style nested structure."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # Missing required work_style fields
        del data["culture"]["work_style"]["collaboration_style"]
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is False
        assert any("work_style" in error and "collaboration_style" in error for error in errors)
    
    def test_validate_yaml_file(self):
        """Test validation of YAML file."""
        # Create valid YAML file
        valid_data = {
            "company_research": CompanyResearchValidator.create_minimal_valid()
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_data, f)
            valid_file = Path(f.name)
        
        try:
            is_valid, errors = CompanyResearchValidator.validate_yaml_file(valid_file)
            assert is_valid is True
            assert errors == []
        finally:
            valid_file.unlink()
        
        # Test invalid YAML file (no company_research key)
        invalid_data = {"wrong_key": {}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_data, f)
            invalid_file = Path(f.name)
        
        try:
            is_valid, errors = CompanyResearchValidator.validate_yaml_file(invalid_file)
            assert is_valid is False
            assert any("company_research" in error for error in errors)
        finally:
            invalid_file.unlink()
    
    def test_format_errors(self):
        """Test error formatting."""
        errors = [
            "Missing required fields: {'culture'}",
            "Field 'mission' too short: 10 chars, minimum 50",
            "Field 'remote_policy' has invalid value 'Sometimes'"
        ]
        
        formatted = CompanyResearchValidator.format_errors(errors)
        assert "Company Research Validation Errors:" in formatted
        assert "1. Missing required fields" in formatted
        assert "2. Field 'mission' too short" in formatted
        assert "3. Field 'remote_policy'" in formatted
        
        # Test no errors
        formatted = CompanyResearchValidator.format_errors([])
        assert formatted == "No errors found"
    
    def test_optional_fields_can_be_missing(self):
        """Test that optional fields can be omitted."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # These fields are optional
        optional_fields = [
            "technology_stack_practices",
            "recent_developments", 
            "market_position_growth"
        ]
        
        # Should be valid without any optional fields
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is True
        
        # Add and remove each optional field
        for field in optional_fields:
            data[field] = {}
            is_valid, errors = CompanyResearchValidator.validate(data)
            assert is_valid is True
            del data[field]
    
    def test_nested_optional_fields(self):
        """Test optional nested fields."""
        data = CompanyResearchValidator.create_minimal_valid()
        
        # reports_to is optional in team_scope
        assert "reports_to" not in data["team_scope"]
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is True
        
        # pace is optional in work_style
        assert "pace" not in data["culture"]["work_style"]
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is True
        
        # Add optional fields
        data["team_scope"]["reports_to"] = "CTO"
        data["culture"]["work_style"]["pace"] = "Fast-paced"
        is_valid, errors = CompanyResearchValidator.validate(data)
        assert is_valid is True