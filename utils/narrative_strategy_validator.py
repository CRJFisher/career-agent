"""
Validator for narrative strategy data structure.

Ensures narrative strategies conform to the schema and contain
all required elements for CV and cover letter generation.
"""

import yaml
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class NarrativeStrategyValidator:
    """Validates narrative strategy structure and content."""
    
    # Required top-level fields
    REQUIRED_FIELDS = {
        "must_tell_experiences",
        "differentiators",
        "career_arc",
        "key_messages",
        "evidence_stories"
    }
    
    # Field constraints
    CONSTRAINTS = {
        "must_tell_experiences": {"min": 2, "max": 3},
        "differentiators": {"min": 1, "max": 2},
        "key_messages": {"min": 3, "max": 3},
        "evidence_stories": {"min": 0, "max": 2}
    }
    
    # Required subfields
    EXPERIENCE_FIELDS = {"title", "reason", "key_points"}
    CAREER_ARC_FIELDS = {"past", "present", "future"}
    STORY_FIELDS = {"title", "challenge", "action", "result", "skills_demonstrated"}
    
    def validate(self, narrative_strategy: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a narrative strategy structure.
        
        Args:
            narrative_strategy: The narrative strategy to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(narrative_strategy.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate each field if present
        if "must_tell_experiences" in narrative_strategy:
            errors.extend(self._validate_experiences(narrative_strategy["must_tell_experiences"]))
        
        if "differentiators" in narrative_strategy:
            errors.extend(self._validate_differentiators(narrative_strategy["differentiators"]))
        
        if "career_arc" in narrative_strategy:
            errors.extend(self._validate_career_arc(narrative_strategy["career_arc"]))
        
        if "key_messages" in narrative_strategy:
            errors.extend(self._validate_key_messages(narrative_strategy["key_messages"]))
        
        if "evidence_stories" in narrative_strategy:
            errors.extend(self._validate_evidence_stories(narrative_strategy["evidence_stories"]))
        
        return len(errors) == 0, errors
    
    def _validate_experiences(self, experiences: Any) -> List[str]:
        """Validate must-tell experiences structure."""
        errors = []
        
        if not isinstance(experiences, list):
            errors.append("must_tell_experiences must be a list")
            return errors
        
        # Check count
        if len(experiences) < self.CONSTRAINTS["must_tell_experiences"]["min"]:
            errors.append(f"must_tell_experiences must have at least {self.CONSTRAINTS['must_tell_experiences']['min']} items")
        if len(experiences) > self.CONSTRAINTS["must_tell_experiences"]["max"]:
            errors.append(f"must_tell_experiences must have at most {self.CONSTRAINTS['must_tell_experiences']['max']} items")
        
        # Validate each experience
        for i, exp in enumerate(experiences):
            if not isinstance(exp, dict):
                errors.append(f"must_tell_experiences[{i}] must be a dictionary")
                continue
            
            # Check required fields
            missing = self.EXPERIENCE_FIELDS - set(exp.keys())
            if missing:
                errors.append(f"must_tell_experiences[{i}] missing fields: {', '.join(missing)}")
            
            # Validate title
            if "title" in exp:
                if not isinstance(exp["title"], str):
                    errors.append(f"must_tell_experiences[{i}].title must be a string")
                elif len(exp["title"]) < 10:
                    errors.append(f"must_tell_experiences[{i}].title too short (min 10 chars)")
            
            # Validate reason
            if "reason" in exp:
                if not isinstance(exp["reason"], str):
                    errors.append(f"must_tell_experiences[{i}].reason must be a string")
                elif len(exp["reason"]) < 20:
                    errors.append(f"must_tell_experiences[{i}].reason too short (min 20 chars)")
            
            # Validate key_points
            if "key_points" in exp:
                if not isinstance(exp["key_points"], list):
                    errors.append(f"must_tell_experiences[{i}].key_points must be a list")
                elif len(exp["key_points"]) < 2:
                    errors.append(f"must_tell_experiences[{i}].key_points must have at least 2 items")
                elif len(exp["key_points"]) > 3:
                    errors.append(f"must_tell_experiences[{i}].key_points must have at most 3 items")
                else:
                    for j, point in enumerate(exp["key_points"]):
                        if not isinstance(point, str):
                            errors.append(f"must_tell_experiences[{i}].key_points[{j}] must be a string")
                        elif len(point) < 10:
                            errors.append(f"must_tell_experiences[{i}].key_points[{j}] too short")
        
        return errors
    
    def _validate_differentiators(self, differentiators: Any) -> List[str]:
        """Validate differentiators list."""
        errors = []
        
        if not isinstance(differentiators, list):
            errors.append("differentiators must be a list")
            return errors
        
        # Check count
        if len(differentiators) < self.CONSTRAINTS["differentiators"]["min"]:
            errors.append(f"differentiators must have at least {self.CONSTRAINTS['differentiators']['min']} items")
        if len(differentiators) > self.CONSTRAINTS["differentiators"]["max"]:
            errors.append(f"differentiators must have at most {self.CONSTRAINTS['differentiators']['max']} items")
        
        # Validate each differentiator
        for i, diff in enumerate(differentiators):
            if not isinstance(diff, str):
                errors.append(f"differentiators[{i}] must be a string")
            elif len(diff) < 20:
                errors.append(f"differentiators[{i}] too short (min 20 chars)")
            elif len(diff) > 200:
                errors.append(f"differentiators[{i}] too long (max 200 chars)")
        
        return errors
    
    def _validate_career_arc(self, career_arc: Any) -> List[str]:
        """Validate career arc structure."""
        errors = []
        
        if not isinstance(career_arc, dict):
            errors.append("career_arc must be a dictionary")
            return errors
        
        # Check required fields
        missing = self.CAREER_ARC_FIELDS - set(career_arc.keys())
        if missing:
            errors.append(f"career_arc missing fields: {', '.join(missing)}")
        
        # Validate each phase
        for phase in ["past", "present", "future"]:
            if phase in career_arc:
                if not isinstance(career_arc[phase], str):
                    errors.append(f"career_arc.{phase} must be a string")
                elif len(career_arc[phase]) < 20:
                    errors.append(f"career_arc.{phase} too short (min 20 chars)")
                elif len(career_arc[phase]) > 150:
                    errors.append(f"career_arc.{phase} too long (max 150 chars)")
        
        # Special check for future - should mention company
        if "future" in career_arc and isinstance(career_arc["future"], str):
            # This is a soft check - logged but not an error
            if not any(word.istitle() for word in career_arc["future"].split()):
                logger.warning("career_arc.future should mention target company")
        
        return errors
    
    def _validate_key_messages(self, messages: Any) -> List[str]:
        """Validate key messages list."""
        errors = []
        
        if not isinstance(messages, list):
            errors.append("key_messages must be a list")
            return errors
        
        # Check count - must be exactly 3
        if len(messages) != self.CONSTRAINTS["key_messages"]["min"]:
            errors.append(f"key_messages must have exactly {self.CONSTRAINTS['key_messages']['min']} items")
        
        # Validate each message
        for i, msg in enumerate(messages):
            if not isinstance(msg, str):
                errors.append(f"key_messages[{i}] must be a string")
            elif len(msg) < 10:
                errors.append(f"key_messages[{i}] too short (min 10 chars)")
            elif len(msg) > 100:
                errors.append(f"key_messages[{i}] too long (max 100 chars)")
        
        return errors
    
    def _validate_evidence_stories(self, stories: Any) -> List[str]:
        """Validate evidence stories structure."""
        errors = []
        
        if not isinstance(stories, list):
            errors.append("evidence_stories must be a list")
            return errors
        
        # Check count
        if len(stories) > self.CONSTRAINTS["evidence_stories"]["max"]:
            errors.append(f"evidence_stories must have at most {self.CONSTRAINTS['evidence_stories']['max']} items")
        
        # Validate each story
        for i, story in enumerate(stories):
            if not isinstance(story, dict):
                errors.append(f"evidence_stories[{i}] must be a dictionary")
                continue
            
            # Check required fields
            missing = self.STORY_FIELDS - set(story.keys())
            if missing:
                errors.append(f"evidence_stories[{i}] missing fields: {', '.join(missing)}")
            
            # Validate CAR components
            for component in ["challenge", "action", "result"]:
                if component in story:
                    if not isinstance(story[component], str):
                        errors.append(f"evidence_stories[{i}].{component} must be a string")
                    elif len(story[component]) < 50:
                        errors.append(f"evidence_stories[{i}].{component} too short (min 50 chars)")
                    elif len(story[component]) > 500:
                        errors.append(f"evidence_stories[{i}].{component} too long (max 500 chars)")
            
            # Validate skills_demonstrated
            if "skills_demonstrated" in story:
                if not isinstance(story["skills_demonstrated"], list):
                    errors.append(f"evidence_stories[{i}].skills_demonstrated must be a list")
                elif len(story["skills_demonstrated"]) < 1:
                    errors.append(f"evidence_stories[{i}].skills_demonstrated must have at least 1 skill")
                elif len(story["skills_demonstrated"]) > 5:
                    errors.append(f"evidence_stories[{i}].skills_demonstrated must have at most 5 skills")
        
        return errors
    
    def validate_yaml_file(self, filepath: str) -> Tuple[bool, List[str]]:
        """
        Validate a narrative strategy from a YAML file.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False, ["Empty YAML file"]
            
            # Handle both wrapped and unwrapped formats
            if "narrative_strategy" in data:
                narrative_strategy = data["narrative_strategy"]
            else:
                narrative_strategy = data
            
            return self.validate(narrative_strategy)
            
        except yaml.YAMLError as e:
            return False, [f"Invalid YAML: {str(e)}"]
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]
    
    def format_errors(self, errors: List[str]) -> str:
        """Format error messages for display."""
        if not errors:
            return "✓ Narrative strategy is valid"
        
        formatted = "✗ Validation errors found:\n"
        for error in errors:
            formatted += f"  - {error}\n"
        return formatted


def validate_integration_compatibility(narrative_strategy: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that narrative strategy is compatible with CV and cover letter generation.
    
    This checks for additional constraints needed by generation flows.
    """
    errors = []
    
    # Must have at least one evidence story OR detailed must-tell experience
    if ("evidence_stories" not in narrative_strategy or 
        len(narrative_strategy.get("evidence_stories", [])) == 0):
        
        # Check if must-tell experiences have enough detail
        must_tells = narrative_strategy.get("must_tell_experiences", [])
        has_detail = any(
            len(exp.get("key_points", [])) >= 2 
            for exp in must_tells 
            if isinstance(exp, dict)
        )
        
        if not has_detail:
            errors.append("Need at least one evidence story or detailed must-tell experience for cover letter")
    
    # Career arc future must be present for cover letter opening
    career_arc = narrative_strategy.get("career_arc", {})
    if not career_arc.get("future"):
        errors.append("career_arc.future required for cover letter opening")
    
    # At least one differentiator needed for unique value proposition
    if not narrative_strategy.get("differentiators"):
        errors.append("At least one differentiator required for unique value proposition")
    
    return len(errors) == 0, errors


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate narrative strategy YAML files")
    parser.add_argument("file", help="Path to narrative strategy YAML file")
    parser.add_argument("--integration", action="store_true", 
                       help="Also check integration compatibility")
    
    args = parser.parse_args()
    
    validator = NarrativeStrategyValidator()
    is_valid, errors = validator.validate_yaml_file(args.file)
    
    print(validator.format_errors(errors))
    
    if is_valid and args.integration:
        # Load and check integration compatibility
        with open(args.file, 'r') as f:
            data = yaml.safe_load(f)
            narrative_strategy = data.get("narrative_strategy", data)
        
        int_valid, int_errors = validate_integration_compatibility(narrative_strategy)
        if int_errors:
            print("\n✗ Integration compatibility issues:")
            for error in int_errors:
                print(f"  - {error}")
        else:
            print("\n✓ Integration compatibility verified")
    
    exit(0 if is_valid else 1)