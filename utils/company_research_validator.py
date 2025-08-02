"""
Company research YAML validator.

Provides validation functions for company research data structure
to ensure it conforms to the defined schema.
"""

from typing import Dict, Any, List, Tuple, Optional
import yaml
from pathlib import Path


class CompanyResearchValidator:
    """Validates company research data against the defined schema."""
    
    # Required top-level fields
    REQUIRED_FIELDS = {
        "mission",
        "team_scope", 
        "strategic_importance",
        "culture"
    }
    
    # Required nested fields
    REQUIRED_NESTED = {
        "team_scope": {"team_name", "size", "responsibilities"},
        "strategic_importance": {"business_impact", "growth_trajectory", "innovation_areas"},
        "culture": {"values", "work_style", "employee_experience"},
        "work_style": {"remote_policy", "collaboration_style"}
    }
    
    # Field type expectations
    FIELD_TYPES = {
        "mission": str,
        "team_scope": dict,
        "strategic_importance": dict,
        "culture": dict,
        "technology_stack_practices": dict,
        "recent_developments": dict,
        "market_position_growth": dict,
        # Nested fields
        "team_name": str,
        "size": str,
        "responsibilities": list,
        "reports_to": str,
        "business_impact": str,
        "growth_trajectory": str,
        "innovation_areas": list,
        "values": list,
        "work_style": dict,
        "employee_experience": dict,
        "remote_policy": str,
        "collaboration_style": str,
        "pace": str
    }
    
    # Minimum lengths for string fields
    MIN_LENGTHS = {
        "mission": 50,
        "business_impact": 50,
        "growth_trajectory": 30
    }
    
    # Maximum lengths for string fields
    MAX_LENGTHS = {
        "mission": 500
    }
    
    # List size constraints
    LIST_CONSTRAINTS = {
        "responsibilities": {"min": 2},
        "values": {"min": 2, "max": 6}
    }
    
    # Enum constraints
    ENUM_VALUES = {
        "remote_policy": {"Remote-first", "Hybrid", "Office-first", "Flexible"}
    }
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate company research data.
        
        Args:
            data: Company research dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        missing_fields = cls.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Validate each field
        for field, value in data.items():
            # Check field type
            if field in cls.FIELD_TYPES:
                expected_type = cls.FIELD_TYPES[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' should be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                    continue
            
            # String validations
            if isinstance(value, str):
                # Check minimum length
                if field in cls.MIN_LENGTHS and len(value) < cls.MIN_LENGTHS[field]:
                    errors.append(
                        f"Field '{field}' too short: {len(value)} chars, "
                        f"minimum {cls.MIN_LENGTHS[field]}"
                    )
                
                # Check maximum length
                if field in cls.MAX_LENGTHS and len(value) > cls.MAX_LENGTHS[field]:
                    errors.append(
                        f"Field '{field}' too long: {len(value)} chars, "
                        f"maximum {cls.MAX_LENGTHS[field]}"
                    )
                
                # Check enum values
                if field in cls.ENUM_VALUES and value not in cls.ENUM_VALUES[field]:
                    errors.append(
                        f"Field '{field}' has invalid value '{value}'. "
                        f"Must be one of: {cls.ENUM_VALUES[field]}"
                    )
            
            # List validations
            elif isinstance(value, list):
                if field in cls.LIST_CONSTRAINTS:
                    constraints = cls.LIST_CONSTRAINTS[field]
                    if "min" in constraints and len(value) < constraints["min"]:
                        errors.append(
                            f"Field '{field}' has too few items: {len(value)}, "
                            f"minimum {constraints['min']}"
                        )
                    if "max" in constraints and len(value) > constraints["max"]:
                        errors.append(
                            f"Field '{field}' has too many items: {len(value)}, "
                            f"maximum {constraints['max']}"
                        )
            
            # Nested object validations
            elif isinstance(value, dict) and field in cls.REQUIRED_NESTED:
                required_nested = cls.REQUIRED_NESTED[field]
                missing_nested = required_nested - set(value.keys())
                if missing_nested:
                    errors.append(
                        f"Field '{field}' missing required subfields: {missing_nested}"
                    )
                
                # Recursively validate nested fields
                for nested_field, nested_value in value.items():
                    if nested_field in cls.FIELD_TYPES:
                        expected_type = cls.FIELD_TYPES[nested_field]
                        if not isinstance(nested_value, expected_type):
                            errors.append(
                                f"Field '{field}.{nested_field}' should be "
                                f"{expected_type.__name__}, got {type(nested_value).__name__}"
                            )
                            continue
                    
                    # Apply string validations to nested strings
                    if isinstance(nested_value, str):
                        if nested_field in cls.MIN_LENGTHS and len(nested_value) < cls.MIN_LENGTHS[nested_field]:
                            errors.append(
                                f"Field '{field}.{nested_field}' too short: {len(nested_value)} chars, "
                                f"minimum {cls.MIN_LENGTHS[nested_field]}"
                            )
                        
                        if nested_field in cls.MAX_LENGTHS and len(nested_value) > cls.MAX_LENGTHS[nested_field]:
                            errors.append(
                                f"Field '{field}.{nested_field}' too long: {len(nested_value)} chars, "
                                f"maximum {cls.MAX_LENGTHS[nested_field]}"
                            )
                    
                    # Apply list validations to nested lists
                    elif isinstance(nested_value, list):
                        if nested_field in cls.LIST_CONSTRAINTS:
                            constraints = cls.LIST_CONSTRAINTS[nested_field]
                            if "min" in constraints and len(nested_value) < constraints["min"]:
                                errors.append(
                                    f"Field '{field}.{nested_field}' has too few items: {len(nested_value)}, "
                                    f"minimum {constraints['min']}"
                                )
                            if "max" in constraints and len(nested_value) > constraints["max"]:
                                errors.append(
                                    f"Field '{field}.{nested_field}' has too many items: {len(nested_value)}, "
                                    f"maximum {constraints['max']}"
                                )
        
        # Special validation for work_style
        if "culture" in data and isinstance(data["culture"], dict):
            if "work_style" in data["culture"]:
                work_style = data["culture"]["work_style"]
                if isinstance(work_style, dict):
                    # Check nested required fields
                    required = cls.REQUIRED_NESTED.get("work_style", set())
                    missing = required - set(work_style.keys())
                    if missing:
                        errors.append(
                            f"Field 'culture.work_style' missing required subfields: {missing}"
                        )
                    
                    # Check remote_policy enum
                    if "remote_policy" in work_style:
                        policy = work_style["remote_policy"]
                        if policy not in cls.ENUM_VALUES["remote_policy"]:
                            errors.append(
                                f"Field 'culture.work_style.remote_policy' has invalid "
                                f"value '{policy}'. Must be one of: "
                                f"{cls.ENUM_VALUES['remote_policy']}"
                            )
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_yaml_file(cls, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Validate a YAML file containing company research.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                return False, ["YAML file must contain a dictionary at top level"]
            
            # Check for company_research key
            if "company_research" not in data:
                return False, ["YAML must have 'company_research' as top-level key"]
            
            return cls.validate(data["company_research"])
            
        except yaml.YAMLError as e:
            return False, [f"Invalid YAML: {str(e)}"]
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]
    
    @classmethod
    def create_minimal_valid(cls) -> Dict[str, Any]:
        """
        Create a minimal valid company research structure.
        
        Returns:
            Dictionary with all required fields populated with minimal valid values
        """
        return {
            "mission": "A" * 50,  # Minimum length mission
            "team_scope": {
                "team_name": "Engineering Team",
                "size": "5-10 people",
                "responsibilities": ["Responsibility 1", "Responsibility 2"]
            },
            "strategic_importance": {
                "business_impact": "B" * 50,  # Minimum length impact
                "growth_trajectory": "G" * 30,  # Minimum length trajectory
                "innovation_areas": ["Area 1", "Area 2"]
            },
            "culture": {
                "values": ["Value 1", "Value 2"],
                "work_style": {
                    "remote_policy": "Hybrid",
                    "collaboration_style": "Agile teams"
                },
                "employee_experience": {}
            }
        }
    
    @classmethod
    def format_errors(cls, errors: List[str]) -> str:
        """
        Format error messages for display.
        
        Args:
            errors: List of error messages
            
        Returns:
            Formatted error string
        """
        if not errors:
            return "No errors found"
        
        formatted = "Company Research Validation Errors:\n"
        for i, error in enumerate(errors, 1):
            formatted += f"  {i}. {error}\n"
        
        return formatted