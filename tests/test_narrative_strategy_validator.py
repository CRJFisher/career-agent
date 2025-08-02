"""
Tests for narrative strategy validator.

Tests validation rules, constraints, and integration compatibility checks.
"""

import pytest
from typing import Dict, Any
import tempfile
import yaml

from utils.narrative_strategy_validator import (
    NarrativeStrategyValidator,
    validate_integration_compatibility
)


class TestNarrativeStrategyValidator:
    """Test suite for NarrativeStrategyValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return NarrativeStrategyValidator()
    
    @pytest.fixture
    def valid_strategy(self):
        """Create a valid narrative strategy."""
        return {
            "must_tell_experiences": [
                {
                    "title": "Senior Software Engineer at TechCorp",
                    "reason": "Directly demonstrates platform engineering and leadership",
                    "key_points": [
                        "Led team of 5 engineers on platform",
                        "Reduced latency by 40% through optimization"
                    ]
                },
                {
                    "title": "ML Pipeline Automation Project",
                    "reason": "Shows innovation and automation mindset crucial for role",
                    "key_points": [
                        "Automated ML deployment reducing time 90%",
                        "Built Kubernetes platform for scale"
                    ]
                }
            ],
            "differentiators": [
                "Rare combination of low-level optimization and high-level architecture"
            ],
            "career_arc": {
                "past": "Started as developer, found passion for systems",
                "present": "Leading platform initiatives for engineering teams",
                "future": "Ready to architect platforms at InnovateTech"
            },
            "key_messages": [
                "Platform expertise enabling business growth",
                "Leadership combining technical excellence with mentorship",
                "Track record of on-time delivery with impact"
            ],
            "evidence_stories": [
                {
                    "title": "Microservices Platform Transformation",
                    "challenge": "Monolithic architecture was blocking 50+ developers and causing daily outages needing complete overhaul",
                    "action": "Led team to design microservices platform with service mesh and GitOps CI/CD while mentoring on patterns",
                    "result": "Delivered 2 weeks early reducing deployment from days to 30 minutes and enabling 3x faster delivery",
                    "skills_demonstrated": ["Platform Architecture", "Team Leadership"]
                }
            ]
        }
    
    def test_valid_strategy_passes(self, validator, valid_strategy):
        """Test that a valid strategy passes validation."""
        is_valid, errors = validator.validate(valid_strategy)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_fields(self, validator):
        """Test detection of missing required fields."""
        incomplete = {
            "must_tell_experiences": [],
            "career_arc": {}
            # Missing: differentiators, key_messages, evidence_stories
        }
        
        is_valid, errors = validator.validate(incomplete)
        assert not is_valid
        assert any("Missing required fields" in err for err in errors)
        assert any("differentiators" in err for err in errors)
    
    def test_must_tell_experiences_validation(self, validator):
        """Test must_tell_experiences validation rules."""
        # Too few experiences
        strategy = {
            "must_tell_experiences": [
                {
                    "title": "Single Experience Only",
                    "reason": "This is the only experience I have",
                    "key_points": ["Point 1", "Point 2"]
                }
            ],
            "differentiators": ["Unique skill"],
            "career_arc": {"past": "p" * 20, "present": "p" * 20, "future": "f" * 20},
            "key_messages": ["m1", "m2", "m3"],
            "evidence_stories": []
        }
        
        is_valid, errors = validator.validate(strategy)
        assert not is_valid
        assert any("must_tell_experiences must have at least 2" in err for err in errors)
        
        # Missing required fields in experience
        strategy["must_tell_experiences"] = [
            {"title": "Missing fields experience"},  # Missing reason and key_points
            {"title": "Another experience", "reason": "Valid reason", "key_points": ["p1", "p2"]}
        ]
        
        is_valid, errors = validator.validate(strategy)
        assert not is_valid
        assert any("missing fields" in err for err in errors)
    
    def test_experience_field_constraints(self, validator, valid_strategy):
        """Test field length constraints in experiences."""
        # Title too short
        valid_strategy["must_tell_experiences"][0]["title"] = "Short"
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("title too short" in err for err in errors)
        
        # Reason too short
        valid_strategy["must_tell_experiences"][0]["title"] = "Valid Title Here"
        valid_strategy["must_tell_experiences"][0]["reason"] = "Too short"
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("reason too short" in err for err in errors)
        
        # Key points constraints
        valid_strategy["must_tell_experiences"][0]["reason"] = "This is a valid reason for selection"
        valid_strategy["must_tell_experiences"][0]["key_points"] = ["Only one"]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("key_points must have at least 2" in err for err in errors)
    
    def test_differentiators_validation(self, validator, valid_strategy):
        """Test differentiators validation."""
        # Empty differentiators
        valid_strategy["differentiators"] = []
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("differentiators must have at least 1" in err for err in errors)
        
        # Too many differentiators
        valid_strategy["differentiators"] = [
            "First differentiator that is long enough",
            "Second differentiator that is long enough",
            "Third differentiator that is too many"
        ]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("differentiators must have at most 2" in err for err in errors)
        
        # Differentiator too short
        valid_strategy["differentiators"] = ["Too short"]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("differentiators[0] too short" in err for err in errors)
    
    def test_career_arc_validation(self, validator, valid_strategy):
        """Test career arc validation."""
        # Missing required phases
        valid_strategy["career_arc"] = {"past": "Valid past description here"}
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("career_arc missing fields" in err for err in errors)
        
        # Phase too short
        valid_strategy["career_arc"] = {
            "past": "Too short",
            "present": "Valid present description goes here",
            "future": "Valid future description at company"
        }
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("career_arc.past too short" in err for err in errors)
    
    def test_key_messages_validation(self, validator, valid_strategy):
        """Test key messages validation."""
        # Wrong number of messages
        valid_strategy["key_messages"] = ["Message 1", "Message 2"]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("key_messages must have exactly 3" in err for err in errors)
        
        # Message too short
        valid_strategy["key_messages"] = ["Short", "Valid message two", "Valid message three"]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("key_messages[0] too short" in err for err in errors)
    
    def test_evidence_stories_validation(self, validator, valid_strategy):
        """Test evidence stories validation."""
        # Invalid story structure
        valid_strategy["evidence_stories"] = [
            {
                "title": "Incomplete Story",
                "challenge": "Only has challenge"
                # Missing action, result, skills_demonstrated
            }
        ]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("evidence_stories[0] missing fields" in err for err in errors)
        
        # CAR components too short
        valid_strategy["evidence_stories"] = [
            {
                "title": "Story with Short Components",
                "challenge": "Too short",
                "action": "Led team to implement solution with multiple technical components involved",
                "result": "Delivered on time with significant impact reducing costs and time",
                "skills_demonstrated": ["Leadership"]
            }
        ]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("challenge too short" in err for err in errors)
        
        # Too many stories
        valid_story = valid_strategy["evidence_stories"][0]
        valid_strategy["evidence_stories"] = [valid_story, valid_story, valid_story]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("evidence_stories must have at most 2" in err for err in errors)
    
    def test_validate_yaml_file(self, validator, valid_strategy):
        """Test YAML file validation."""
        # Test with wrapped format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"narrative_strategy": valid_strategy}, f)
            filepath = f.name
        
        is_valid, errors = validator.validate_yaml_file(filepath)
        assert is_valid
        assert len(errors) == 0
        
        # Test with unwrapped format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_strategy, f)
            filepath = f.name
        
        is_valid, errors = validator.validate_yaml_file(filepath)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_yaml_file(self, validator):
        """Test handling of invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [[[")
            filepath = f.name
        
        is_valid, errors = validator.validate_yaml_file(filepath)
        assert not is_valid
        assert any("Invalid YAML" in err for err in errors)
    
    def test_format_errors(self, validator):
        """Test error formatting."""
        errors = ["Error 1", "Error 2", "Error 3"]
        formatted = validator.format_errors(errors)
        
        assert "✗ Validation errors found:" in formatted
        assert "- Error 1" in formatted
        assert "- Error 2" in formatted
        assert "- Error 3" in formatted
        
        # Test success case
        formatted = validator.format_errors([])
        assert "✓ Narrative strategy is valid" in formatted
    
    def test_integration_compatibility(self, valid_strategy):
        """Test integration compatibility checks."""
        # Valid strategy should pass
        is_valid, errors = validate_integration_compatibility(valid_strategy)
        assert is_valid
        assert len(errors) == 0
        
        # No evidence stories and minimal must-tells
        strategy = valid_strategy.copy()
        strategy["evidence_stories"] = []
        strategy["must_tell_experiences"] = [
            {"title": "Experience 1", "reason": "Reason", "key_points": ["Point"]},
            {"title": "Experience 2", "reason": "Reason", "key_points": ["Point"]}
        ]
        is_valid, errors = validate_integration_compatibility(strategy)
        assert not is_valid
        assert any("evidence story or detailed must-tell" in err for err in errors)
        
        # Missing career arc future
        strategy = valid_strategy.copy()
        strategy["career_arc"]["future"] = ""
        is_valid, errors = validate_integration_compatibility(strategy)
        assert not is_valid
        assert any("career_arc.future required" in err for err in errors)
        
        # No differentiators
        strategy = valid_strategy.copy()
        strategy["differentiators"] = []
        is_valid, errors = validate_integration_compatibility(strategy)
        assert not is_valid
        assert any("differentiator required" in err for err in errors)
    
    def test_type_validation(self, validator):
        """Test type validation for fields."""
        strategy = {
            "must_tell_experiences": "not a list",  # Should be list
            "differentiators": ["Valid differentiator here"],
            "career_arc": {"past": "p" * 20, "present": "p" * 20, "future": "f" * 20},
            "key_messages": ["m1", "m2", "m3"],
            "evidence_stories": []
        }
        
        is_valid, errors = validator.validate(strategy)
        assert not is_valid
        assert any("must_tell_experiences must be a list" in err for err in errors)
        
        # Dict fields as wrong type
        strategy["must_tell_experiences"] = [{"title": "t" * 20, "reason": "r" * 20, "key_points": ["p1", "p2"]}] * 2
        strategy["career_arc"] = ["not", "a", "dict"]
        
        is_valid, errors = validator.validate(strategy)
        assert not is_valid
        assert any("career_arc must be a dictionary" in err for err in errors)
    
    def test_skills_demonstrated_validation(self, validator, valid_strategy):
        """Test skills_demonstrated in evidence stories."""
        # No skills
        valid_strategy["evidence_stories"][0]["skills_demonstrated"] = []
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("skills_demonstrated must have at least 1" in err for err in errors)
        
        # Too many skills
        valid_strategy["evidence_stories"][0]["skills_demonstrated"] = [
            "Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5", "Skill 6"
        ]
        is_valid, errors = validator.validate(valid_strategy)
        assert not is_valid
        assert any("skills_demonstrated must have at most 5" in err for err in errors)
    
    def test_edge_cases(self, validator):
        """Test edge cases and boundary conditions."""
        # Empty strategy
        is_valid, errors = validator.validate({})
        assert not is_valid
        assert any("Missing required fields" in err for err in errors)
        
        # Minimal valid strategy (0 evidence stories allowed)
        minimal = {
            "must_tell_experiences": [
                {"title": "Experience One Title", "reason": "Valid reason for selection here", 
                 "key_points": ["First key point here", "Second key point here"]},
                {"title": "Experience Two Title", "reason": "Another valid reason for selection", 
                 "key_points": ["Another first point", "Another second point"]}
            ],
            "differentiators": ["Unique value proposition that sets me apart"],
            "career_arc": {
                "past": "Started career with strong foundation",
                "present": "Currently leading important initiatives",
                "future": "Ready to contribute at TargetCompany"
            },
            "key_messages": [
                "First key message here",
                "Second key message here",
                "Third key message here"
            ],
            "evidence_stories": []  # Allowed to be empty
        }
        
        is_valid, errors = validator.validate(minimal)
        assert is_valid
        assert len(errors) == 0