"""
Tests for shared store validation functionality.
"""

import unittest
from datetime import datetime

from utils.shared_store_validator import (
    SharedStoreValidator,
    validate_shared_store,
    log_validation_warnings
)


class TestSharedStoreValidator(unittest.TestCase):
    """Test the SharedStoreValidator class."""
    
    def test_validate_type_correct_types(self):
        """Test type validation with correct types."""
        # Test string type
        valid, error = SharedStoreValidator.validate_type("job_title", "Software Engineer")
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # Test dict type
        valid, error = SharedStoreValidator.validate_type("career_db", {"experience": []})
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # Test optional type (str or None)
        valid, error = SharedStoreValidator.validate_type("company_url", None)
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        valid, error = SharedStoreValidator.validate_type("company_url", "https://example.com")
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        # Test numeric type (int or float)
        valid, error = SharedStoreValidator.validate_type("coverage_score", 85.5)
        self.assertTrue(valid)
        self.assertIsNone(error)
    
    def test_validate_type_incorrect_types(self):
        """Test type validation with incorrect types."""
        # String instead of dict
        valid, error = SharedStoreValidator.validate_type("career_db", "not a dict")
        self.assertFalse(valid)
        self.assertIn("must be type dict", error)
        
        # Int instead of string
        valid, error = SharedStoreValidator.validate_type("job_title", 123)
        self.assertFalse(valid)
        self.assertIn("must be type str", error)
        
        # Dict instead of list
        valid, error = SharedStoreValidator.validate_type("gaps", {})
        self.assertFalse(valid)
        self.assertIn("must be type list", error)
    
    def test_validate_flow_requirements(self):
        """Test flow requirement validation."""
        # Valid shared store for RequirementMappingNode
        shared = {
            "career_db": {"experience": []},
            "requirements": {"required": ["Python"]}
        }
        valid, errors = SharedStoreValidator.validate_flow_requirements(
            shared, "RequirementMappingNode"
        )
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Missing required field
        shared = {"career_db": {"experience": []}}
        valid, errors = SharedStoreValidator.validate_flow_requirements(
            shared, "RequirementMappingNode"
        )
        self.assertFalse(valid)
        self.assertIn("Missing required key 'requirements'", errors[0])
        
        # Required field is None
        shared = {
            "career_db": {"experience": []},
            "requirements": None
        }
        valid, errors = SharedStoreValidator.validate_flow_requirements(
            shared, "RequirementMappingNode"
        )
        self.assertFalse(valid)
        self.assertIn("Required key 'requirements' is None", errors[0])
    
    def test_validate_requirements_structure(self):
        """Test requirements dictionary validation."""
        # Valid requirements
        requirements = {
            "required": ["Python", "Django"],
            "nice_to_have": ["Kubernetes"],
            "about_role": "Backend engineer role"
        }
        valid, errors = SharedStoreValidator.validate_requirements_structure(requirements)
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Missing required field
        requirements = {"nice_to_have": ["Kubernetes"]}
        valid, errors = SharedStoreValidator.validate_requirements_structure(requirements)
        self.assertFalse(valid)
        self.assertIn("missing 'required' field", errors[0])
        
        # Wrong type for required field
        requirements = {"required": "Python"}  # Should be list
        valid, errors = SharedStoreValidator.validate_requirements_structure(requirements)
        self.assertFalse(valid)
        self.assertIn("must be a list", errors[0])
    
    def test_validate_mapping_structure(self):
        """Test requirement mapping validation."""
        # Valid mapping
        mapping = [
            {
                "requirement": "Python experience",
                "evidence": ["3 years Python at TechCorp"],
                "strength": "HIGH"
            }
        ]
        valid, errors = SharedStoreValidator.validate_mapping_structure(
            mapping, "requirement_mapping_assessed"
        )
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Missing evidence field
        mapping = [{"requirement": "Python experience"}]
        valid, errors = SharedStoreValidator.validate_mapping_structure(
            mapping, "requirement_mapping_raw"
        )
        self.assertFalse(valid)
        self.assertIn("missing 'evidence' field", errors[0])
        
        # Invalid strength value
        mapping = [
            {
                "requirement": "Python",
                "evidence": ["Some evidence"],
                "strength": "VERY_HIGH"  # Invalid
            }
        ]
        valid, errors = SharedStoreValidator.validate_mapping_structure(
            mapping, "requirement_mapping_assessed"
        )
        self.assertFalse(valid)
        self.assertIn("invalid strength", errors[0])
    
    def test_validate_gaps_structure(self):
        """Test gaps validation."""
        # Valid gaps
        gaps = [
            {
                "requirement": "Kubernetes experience",
                "severity": "NICE_TO_HAVE",
                "mitigation_strategies": ["Highlight Docker experience"],
                "talking_points": ["Willing to learn"]
            }
        ]
        valid, errors = SharedStoreValidator.validate_gaps_structure(gaps)
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Invalid severity
        gaps = [
            {
                "requirement": "Kubernetes",
                "severity": "MEDIUM",  # Should be CRITICAL/IMPORTANT/NICE_TO_HAVE
                "mitigation_strategies": []
            }
        ]
        valid, errors = SharedStoreValidator.validate_gaps_structure(gaps)
        self.assertFalse(valid)
        self.assertIn("invalid severity", errors[0])
    
    def test_validate_suitability_assessment(self):
        """Test suitability assessment validation."""
        # Valid assessment
        assessment = {
            "technical_fit_score": 85,
            "cultural_fit_score": 90,
            "key_strengths": ["Python expertise", "Leadership"],
            "critical_gaps": [],
            "unique_value_proposition": "Full-stack with ML",
            "overall_recommendation": "Strong candidate"
        }
        valid, errors = SharedStoreValidator.validate_suitability_assessment(assessment)
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Score out of range
        assessment = {
            "technical_fit_score": 150,  # > 100
            "cultural_fit_score": -10    # < 0
        }
        valid, errors = SharedStoreValidator.validate_suitability_assessment(assessment)
        self.assertFalse(valid)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("between 0-100" in e for e in errors))
    
    def test_validate_narrative_strategy(self):
        """Test narrative strategy validation."""
        # Valid strategy
        strategy = {
            "positioning_statement": "Experienced engineer",
            "career_arc": {
                "past": "Started in startups",
                "present": "Leading teams",
                "future": "Architecture focus"
            },
            "must_tell_experiences": [],
            "key_messages": ["Technical depth"],
            "differentiators": ["ML + Backend"],
            "evidence_stories": []
        }
        valid, errors = SharedStoreValidator.validate_narrative_strategy(strategy)
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Missing positioning statement
        strategy = {"career_arc": {}}
        valid, errors = SharedStoreValidator.validate_narrative_strategy(strategy)
        self.assertFalse(valid)
        self.assertIn("missing 'positioning_statement'", errors[0])
    
    def test_validate_complete_store(self):
        """Test complete store validation."""
        # Create a valid shared store
        shared = {
            "career_db": {"experience": []},
            "job_spec_text": "Job description",
            "job_title": "Software Engineer",
            "company_name": "TechCorp",
            "company_url": "https://techcorp.com",
            "current_date": "2024-01-15",
            "requirements": {"required": ["Python"]},
            "coverage_score": 85.5,
            "enable_company_research": True,
            "max_research_iterations": 15,
            "enable_checkpoints": True
        }
        
        valid, errors = SharedStoreValidator.validate_complete_store(shared)
        self.assertTrue(valid)
        self.assertEqual(errors, [])
        
        # Add invalid type
        shared["coverage_score"] = "not a number"
        valid, errors = SharedStoreValidator.validate_complete_store(shared)
        self.assertFalse(valid)
        self.assertTrue(any("coverage_score" in e for e in errors))


class TestValidationHelperFunctions(unittest.TestCase):
    """Test the helper validation functions."""
    
    def test_validate_shared_store_success(self):
        """Test validate_shared_store with valid data."""
        shared = {
            "career_db": {"experience": []},
            "requirements": {"required": ["Python"]}
        }
        
        # Should not raise exception
        validate_shared_store(shared, "RequirementMappingNode")
    
    def test_validate_shared_store_failure(self):
        """Test validate_shared_store with invalid data."""
        shared = {
            "career_db": "not a dict"  # Wrong type
        }
        
        with self.assertRaises(ValueError) as context:
            validate_shared_store(shared)
        
        self.assertIn("validation failed", str(context.exception))
    
    def test_validate_shared_store_missing_flow_requirements(self):
        """Test validate_shared_store with missing flow requirements."""
        shared = {
            "career_db": {"experience": []}
            # Missing requirements for RequirementMappingNode
        }
        
        with self.assertRaises(ValueError) as context:
            validate_shared_store(shared, "RequirementMappingNode")
        
        self.assertIn("Missing required key 'requirements'", str(context.exception))
    
    def test_log_validation_warnings(self):
        """Test warning logging for potential issues."""
        import logging
        
        # Capture log output
        with self.assertLogs('utils.shared_store_validator', level='WARNING') as cm:
            shared = {
                "requirements": None,
                "cv_markdown": None,
                "coverage_score": 65,  # Low score
                "suitability_assessment": {
                    "technical_fit_score": 60,  # Low score
                    "cultural_fit_score": 65   # Low score
                }
            }
            
            log_validation_warnings(shared)
        
        # Check warnings were logged
        warnings = [record.getMessage() for record in cm.records]
        self.assertTrue(any("output fields are None" in w for w in warnings))
        self.assertTrue(any("Low coverage score" in w for w in warnings))
        self.assertTrue(any("Low technical fit score" in w for w in warnings))
        self.assertTrue(any("Low cultural fit score" in w for w in warnings))


class TestDataContractCompliance(unittest.TestCase):
    """Test that the data contract matches actual usage."""
    
    def test_initial_shared_store_matches_contract(self):
        """Test that initialize_shared_store creates valid structure."""
        from main import initialize_shared_store
        
        shared = initialize_shared_store(
            career_db={"test": "db"},
            job_description="Test job",
            job_title="Engineer",
            company_name="Corp"
        )
        
        # Validate against contract
        valid, errors = SharedStoreValidator.validate_complete_store(shared)
        self.assertTrue(valid, f"Initial shared store invalid: {errors}")
        
        # Check all contract keys are present
        for key in SharedStoreValidator.DATA_CONTRACT.keys():
            self.assertIn(key, shared, f"Missing contract key: {key}")
    
    def test_flow_requirements_match_actual_usage(self):
        """Test that flow requirements match what flows actually need."""
        # This is more of a documentation test
        # Verify that FLOW_REQUIREMENTS matches actual node prep methods
        
        flow_requirements = SharedStoreValidator.FLOW_REQUIREMENTS
        
        # Check some known requirements
        self.assertIn("career_db", flow_requirements["RequirementMappingNode"])
        self.assertIn("requirements", flow_requirements["RequirementMappingNode"])
        self.assertIn("narrative_strategy", flow_requirements["CVGenerationNode"])
        self.assertIn("company_name", flow_requirements["CompanyResearchAgent"])


if __name__ == "__main__":
    unittest.main()