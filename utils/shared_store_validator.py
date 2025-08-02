"""
Shared store validation utilities.

Provides functions to validate the shared store data contract,
ensuring type consistency and required fields across flows.
"""

from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SharedStoreValidator:
    """Validates shared store contents against the data contract."""
    
    # Define expected types for each key
    DATA_CONTRACT = {
        # Initial setup keys
        "career_db": dict,
        "job_spec_text": str,
        "job_description": str,
        "job_title": str,
        "company_name": str,
        "company_url": (str, type(None)),
        "current_date": str,
        
        # Flow output keys
        "requirements": dict,
        "requirement_mapping_raw": list,
        "requirement_mapping_assessed": list,
        "requirement_mapping_final": list,
        "gaps": list,
        "coverage_score": (int, float),
        "company_research": dict,
        "suitability_assessment": dict,
        "prioritized_experiences": list,
        "narrative_strategy": dict,
        "cv_markdown": str,
        "cover_letter_text": str,
        
        # System keys
        "checkpoint_data": dict,
        "enable_company_research": bool,
        "max_research_iterations": int,
        "enable_checkpoints": bool
    }
    
    # Define required fields for specific flows
    FLOW_REQUIREMENTS = {
        "RequirementExtractionFlow": ["career_db", "job_spec_text"],
        "RequirementMappingNode": ["career_db", "requirements"],
        "StrengthAssessmentNode": ["requirement_mapping_raw"],
        "GapAnalysisNode": ["requirement_mapping_assessed"],
        "CompanyResearchAgent": ["company_name"],
        "SuitabilityScoringNode": ["requirement_mapping_final", "gaps", "requirements"],
        "ExperiencePrioritizationNode": ["career_db", "requirement_mapping_final"],
        "NarrativeStrategyNode": ["prioritized_experiences", "suitability_assessment"],
        "CVGenerationNode": ["narrative_strategy", "career_db"],
        "CoverLetterNode": ["narrative_strategy", "career_db", "job_title", "company_name"]
    }
    
    # Valid enum values
    VALID_STRENGTHS = ["HIGH", "MEDIUM", "LOW"]
    VALID_SEVERITIES = ["CRITICAL", "IMPORTANT", "NICE_TO_HAVE"]
    
    @classmethod
    def validate_type(cls, key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value matches the expected type for a key.
        
        Args:
            key: The shared store key
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if key not in cls.DATA_CONTRACT:
            return True, None  # Unknown keys are allowed
        
        expected_types = cls.DATA_CONTRACT[key]
        if not isinstance(expected_types, tuple):
            expected_types = (expected_types,)
        
        if not isinstance(value, expected_types):
            type_names = ", ".join(t.__name__ for t in expected_types)
            return False, f"{key} must be type {type_names}, got {type(value).__name__}"
        
        return True, None
    
    @classmethod
    def validate_flow_requirements(cls, shared: Dict[str, Any], flow_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that shared store has required fields for a specific flow.
        
        Args:
            shared: The shared store dictionary
            flow_name: Name of the flow to validate for
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if flow_name not in cls.FLOW_REQUIREMENTS:
            return True, []  # No requirements defined
        
        errors = []
        required_keys = cls.FLOW_REQUIREMENTS[flow_name]
        
        for key in required_keys:
            if key not in shared:
                errors.append(f"Missing required key '{key}' for {flow_name}")
            elif shared[key] is None:
                errors.append(f"Required key '{key}' is None for {flow_name}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_requirements_structure(cls, requirements: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate the requirements dictionary structure."""
        errors = []
        
        if not isinstance(requirements, dict):
            errors.append("Requirements must be a dictionary")
            return False, errors
        
        if "required" not in requirements:
            errors.append("Requirements missing 'required' field")
        elif not isinstance(requirements["required"], list):
            errors.append("Requirements 'required' field must be a list")
        
        if "nice_to_have" in requirements and not isinstance(requirements["nice_to_have"], list):
            errors.append("Requirements 'nice_to_have' field must be a list")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_mapping_structure(cls, mapping: List[Dict[str, Any]], mapping_type: str) -> Tuple[bool, List[str]]:
        """Validate requirement mapping structure."""
        errors = []
        
        if not isinstance(mapping, list):
            errors.append(f"{mapping_type} must be a list")
            return False, errors
        
        for i, item in enumerate(mapping):
            if not isinstance(item, dict):
                errors.append(f"{mapping_type}[{i}] must be a dictionary")
                continue
            
            # Check required fields
            if "requirement" not in item:
                errors.append(f"{mapping_type}[{i}] missing 'requirement' field")
            if "evidence" not in item:
                errors.append(f"{mapping_type}[{i}] missing 'evidence' field")
            elif not isinstance(item["evidence"], list):
                errors.append(f"{mapping_type}[{i}] 'evidence' must be a list")
            
            # Check strength field for assessed/final mappings
            if mapping_type in ["requirement_mapping_assessed", "requirement_mapping_final"]:
                if "strength" not in item:
                    errors.append(f"{mapping_type}[{i}] missing 'strength' field")
                elif item["strength"] not in cls.VALID_STRENGTHS:
                    errors.append(f"{mapping_type}[{i}] invalid strength: {item['strength']}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_gaps_structure(cls, gaps: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate gaps list structure."""
        errors = []
        
        if not isinstance(gaps, list):
            errors.append("Gaps must be a list")
            return False, errors
        
        for i, gap in enumerate(gaps):
            if not isinstance(gap, dict):
                errors.append(f"gaps[{i}] must be a dictionary")
                continue
            
            # Check required fields
            required_fields = ["requirement", "severity", "mitigation_strategies"]
            for field in required_fields:
                if field not in gap:
                    errors.append(f"gaps[{i}] missing '{field}' field")
            
            # Validate severity
            if "severity" in gap and gap["severity"] not in cls.VALID_SEVERITIES:
                errors.append(f"gaps[{i}] invalid severity: {gap['severity']}")
            
            # Validate mitigation_strategies is a list
            if "mitigation_strategies" in gap and not isinstance(gap["mitigation_strategies"], list):
                errors.append(f"gaps[{i}] 'mitigation_strategies' must be a list")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_suitability_assessment(cls, assessment: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate suitability assessment structure."""
        errors = []
        
        if not isinstance(assessment, dict):
            errors.append("Suitability assessment must be a dictionary")
            return False, errors
        
        # Check score fields
        score_fields = ["technical_fit_score", "cultural_fit_score"]
        for field in score_fields:
            if field not in assessment:
                errors.append(f"Suitability assessment missing '{field}'")
            elif not isinstance(assessment[field], (int, float)):
                errors.append(f"Suitability assessment '{field}' must be numeric")
            elif not 0 <= assessment[field] <= 100:
                errors.append(f"Suitability assessment '{field}' must be between 0-100")
        
        # Check list fields
        list_fields = ["key_strengths", "critical_gaps"]
        for field in list_fields:
            if field in assessment and not isinstance(assessment[field], list):
                errors.append(f"Suitability assessment '{field}' must be a list")
        
        # Check string fields
        string_fields = ["unique_value_proposition", "overall_recommendation"]
        for field in string_fields:
            if field in assessment and not isinstance(assessment[field], str):
                errors.append(f"Suitability assessment '{field}' must be a string")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_narrative_strategy(cls, strategy: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate narrative strategy structure."""
        errors = []
        
        if not isinstance(strategy, dict):
            errors.append("Narrative strategy must be a dictionary")
            return False, errors
        
        # Check required string fields
        if "positioning_statement" not in strategy:
            errors.append("Narrative strategy missing 'positioning_statement'")
        
        # Check career arc
        if "career_arc" in strategy:
            if not isinstance(strategy["career_arc"], dict):
                errors.append("Narrative strategy 'career_arc' must be a dictionary")
            else:
                for phase in ["past", "present", "future"]:
                    if phase not in strategy["career_arc"]:
                        errors.append(f"Career arc missing '{phase}' field")
        
        # Check list fields
        list_fields = ["must_tell_experiences", "key_messages", "differentiators", "evidence_stories"]
        for field in list_fields:
            if field in strategy and not isinstance(strategy[field], list):
                errors.append(f"Narrative strategy '{field}' must be a list")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_complete_store(cls, shared: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Perform complete validation of shared store.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate types
        for key, value in shared.items():
            if value is not None:  # Skip None values
                valid, error = cls.validate_type(key, value)
                if not valid:
                    errors.append(error)
        
        # Validate specific structures
        if "requirements" in shared and shared["requirements"] is not None:
            valid, req_errors = cls.validate_requirements_structure(shared["requirements"])
            errors.extend(req_errors)
        
        if "requirement_mapping_raw" in shared and shared["requirement_mapping_raw"] is not None:
            valid, map_errors = cls.validate_mapping_structure(
                shared["requirement_mapping_raw"], "requirement_mapping_raw"
            )
            errors.extend(map_errors)
        
        if "gaps" in shared and shared["gaps"] is not None:
            valid, gap_errors = cls.validate_gaps_structure(shared["gaps"])
            errors.extend(gap_errors)
        
        if "suitability_assessment" in shared and shared["suitability_assessment"] is not None:
            valid, assess_errors = cls.validate_suitability_assessment(shared["suitability_assessment"])
            errors.extend(assess_errors)
        
        if "narrative_strategy" in shared and shared["narrative_strategy"] is not None:
            valid, narr_errors = cls.validate_narrative_strategy(shared["narrative_strategy"])
            errors.extend(narr_errors)
        
        return len(errors) == 0, errors


def validate_shared_store(shared: Dict[str, Any], flow_name: Optional[str] = None) -> None:
    """
    Validate shared store and raise exception if invalid.
    
    Args:
        shared: The shared store dictionary
        flow_name: Optional flow name to validate requirements for
        
    Raises:
        ValueError: If validation fails
    """
    # Validate complete store
    valid, errors = SharedStoreValidator.validate_complete_store(shared)
    
    # Validate flow requirements if specified
    if flow_name:
        flow_valid, flow_errors = SharedStoreValidator.validate_flow_requirements(shared, flow_name)
        valid = valid and flow_valid
        errors.extend(flow_errors)
    
    if not valid:
        error_msg = "Shared store validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)


def log_validation_warnings(shared: Dict[str, Any]) -> None:
    """
    Log warnings for potential issues that don't fail validation.
    
    Args:
        shared: The shared store dictionary
    """
    # Warn about None values in output fields
    output_fields = [
        "requirements", "requirement_mapping_final", "gaps",
        "suitability_assessment", "narrative_strategy",
        "cv_markdown", "cover_letter_text"
    ]
    
    none_fields = [f for f in output_fields if shared.get(f) is None]
    if none_fields:
        logger.warning(f"The following output fields are None: {', '.join(none_fields)}")
    
    # Warn about missing optional fields
    if "company_research" not in shared or shared["company_research"] is None:
        logger.warning("No company research available - output may be generic")
    
    # Warn about low scores
    if "coverage_score" in shared and shared["coverage_score"] is not None:
        if shared["coverage_score"] < 70:
            logger.warning(f"Low coverage score: {shared['coverage_score']}%")
    
    if "suitability_assessment" in shared and shared["suitability_assessment"] is not None:
        assessment = shared["suitability_assessment"]
        if assessment.get("technical_fit_score", 100) < 70:
            logger.warning(f"Low technical fit score: {assessment['technical_fit_score']}%")
        if assessment.get("cultural_fit_score", 100) < 70:
            logger.warning(f"Low cultural fit score: {assessment['cultural_fit_score']}%")