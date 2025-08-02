"""
Analyzes the effectiveness of the suitability assessment prompt.

This module provides tools to evaluate prompt quality, consistency,
and coverage across various candidate scenarios.
"""

from typing import Dict, Any, List, Tuple, Optional
import yaml
import re
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class PromptMetrics:
    """Metrics for evaluating prompt effectiveness."""
    
    # Structural metrics
    total_words: int
    instruction_clarity_score: float  # 0-1
    example_coverage: float  # 0-1
    output_specification_completeness: float  # 0-1
    
    # Content metrics
    role_definition_strength: float  # 0-1
    scoring_methodology_clarity: float  # 0-1
    framework_definitions: int  # Count of frameworks provided
    edge_case_handling: float  # 0-1
    
    # Instruction quality
    specificity_score: float  # 0-1
    actionability_score: float  # 0-1
    consistency_guidelines: float  # 0-1
    
    def overall_score(self) -> float:
        """Calculate overall prompt effectiveness score."""
        scores = [
            self.instruction_clarity_score,
            self.example_coverage,
            self.output_specification_completeness,
            self.role_definition_strength,
            self.scoring_methodology_clarity,
            min(self.framework_definitions / 3, 1.0),  # Expect at least 3 frameworks
            self.edge_case_handling,
            self.specificity_score,
            self.actionability_score,
            self.consistency_guidelines
        ]
        return sum(scores) / len(scores)


class PromptEffectivenessAnalyzer:
    """Analyzes suitability assessment prompt effectiveness."""
    
    # Key sections expected in a good prompt
    EXPECTED_SECTIONS = [
        "role definition",
        "technical fit", 
        "cultural fit",
        "scoring methodology",
        "strength identification",
        "gap analysis",
        "unique value proposition",
        "output format",
        "example"
    ]
    
    # Frameworks that should be defined
    EXPECTED_FRAMEWORKS = [
        "STAR-V",  # Strength identification
        "Cultural Fit Dimensions",
        "Gap Significance Levels",
        "Venn Diagram"  # UVP identification
    ]
    
    # Output fields that must be specified
    REQUIRED_OUTPUT_FIELDS = [
        "cultural_fit_score",
        "cultural_fit_breakdown",
        "key_strengths",
        "critical_gaps",
        "unique_value_proposition",
        "hiring_recommendation",
        "interview_focus_areas"
    ]
    
    def analyze_prompt(self, prompt_text: str) -> PromptMetrics:
        """
        Analyze a prompt and return effectiveness metrics.
        
        Args:
            prompt_text: The prompt text to analyze
            
        Returns:
            PromptMetrics with scored dimensions
        """
        metrics = PromptMetrics(
            total_words=len(prompt_text.split()),
            instruction_clarity_score=self._score_clarity(prompt_text),
            example_coverage=self._score_examples(prompt_text),
            output_specification_completeness=self._score_output_spec(prompt_text),
            role_definition_strength=self._score_role_definition(prompt_text),
            scoring_methodology_clarity=self._score_methodology(prompt_text),
            framework_definitions=self._count_frameworks(prompt_text),
            edge_case_handling=self._score_edge_cases(prompt_text),
            specificity_score=self._score_specificity(prompt_text),
            actionability_score=self._score_actionability(prompt_text),
            consistency_guidelines=self._score_consistency(prompt_text)
        )
        
        return metrics
    
    def _score_clarity(self, prompt: str) -> float:
        """Score instruction clarity (0-1)."""
        clarity_indicators = [
            "you are",  # Clear role
            "your task",  # Clear objective
            "must", "should",  # Clear requirements
            "step", "first", "then",  # Sequential instructions
            "specifically",  # Specific guidance
        ]
        
        lower_prompt = prompt.lower()
        found = sum(1 for indicator in clarity_indicators if indicator in lower_prompt)
        return min(found / len(clarity_indicators), 1.0)
    
    def _score_examples(self, prompt: str) -> float:
        """Score example coverage (0-1)."""
        example_indicators = [
            "example",
            "for instance",
            "e.g.",
            "such as",
            "```"  # Code/format blocks
        ]
        
        lower_prompt = prompt.lower()
        
        # Check for concrete example
        has_detailed_example = "example output" in lower_prompt or "example analysis" in lower_prompt
        
        # Count example indicators
        indicator_count = sum(1 for ind in example_indicators if ind in lower_prompt)
        
        # Bonus for detailed example
        score = min(indicator_count / 3, 1.0)  # Expect at least 3 example indicators
        if has_detailed_example:
            score = min(score + 0.3, 1.0)
        
        return score
    
    def _score_output_spec(self, prompt: str) -> float:
        """Score output specification completeness (0-1)."""
        lower_prompt = prompt.lower()
        
        # Check for output format specification
        has_format = "yaml" in lower_prompt or "json" in lower_prompt
        
        # Check for required fields
        fields_specified = sum(
            1 for field in self.REQUIRED_OUTPUT_FIELDS 
            if field in lower_prompt
        )
        field_coverage = fields_specified / len(self.REQUIRED_OUTPUT_FIELDS)
        
        # Check for field descriptions
        has_descriptions = ":" in prompt and "#" in prompt  # YAML with comments
        
        score = 0.0
        if has_format:
            score += 0.3
        score += field_coverage * 0.5
        if has_descriptions:
            score += 0.2
            
        return min(score, 1.0)
    
    def _score_role_definition(self, prompt: str) -> float:
        """Score role definition strength (0-1)."""
        role_indicators = [
            "senior hiring manager",
            "years of experience",
            "evaluating",
            "technical talent",
            "perspective"
        ]
        
        lower_prompt = prompt.lower()
        found = sum(1 for indicator in role_indicators if indicator in lower_prompt)
        
        # Check for detailed role description
        has_detailed_role = len(re.findall(r'you are.*?\.', lower_prompt, re.DOTALL)) > 0
        
        score = found / len(role_indicators)
        if has_detailed_role:
            score = min(score + 0.2, 1.0)
            
        return score
    
    def _score_methodology(self, prompt: str) -> float:
        """Score scoring methodology clarity (0-1)."""
        methodology_elements = [
            "HIGH strength = 100%",
            "MEDIUM strength = 60%", 
            "LOW strength = 30%",
            "Missing/Gap = 0%",
            "weight",
            "calculation",
            "score"
        ]
        
        found = sum(1 for elem in methodology_elements if elem in prompt)
        return found / len(methodology_elements)
    
    def _count_frameworks(self, prompt: str) -> int:
        """Count number of frameworks defined."""
        count = 0
        lower_prompt = prompt.lower()
        
        for framework in self.EXPECTED_FRAMEWORKS:
            if framework.lower() in lower_prompt:
                count += 1
        
        # Also check for generic framework indicators
        if "framework" in lower_prompt:
            # Count occurrences of the word "framework"
            count += min(prompt.lower().count("framework") // 2, 2)  # Cap at 2 extra
            
        return count
    
    def _score_edge_cases(self, prompt: str) -> float:
        """Score edge case handling (0-1)."""
        edge_case_indicators = [
            "incomplete information",
            "missing",
            "unavailable",
            "limited",
            "edge case",
            "special case",
            "exception"
        ]
        
        lower_prompt = prompt.lower()
        found = sum(1 for indicator in edge_case_indicators if indicator in lower_prompt)
        
        # Look for instruction to handle uncertainty
        has_uncertainty_handling = any(
            phrase in lower_prompt 
            for phrase in ["acknowledge", "caveat", "note any assumptions"]
        )
        
        score = min(found / 3, 0.7)  # Expect at least 3 indicators
        if has_uncertainty_handling:
            score += 0.3
            
        return min(score, 1.0)
    
    def _score_specificity(self, prompt: str) -> float:
        """Score specificity of instructions (0-1)."""
        specificity_indicators = [
            "specifically",
            "exactly", 
            "must include",
            "required",
            "minimum",
            "maximum",
            "between",
            r"\d+",  # Numbers
            "example:"
        ]
        
        score = 0.0
        for indicator in specificity_indicators:
            if re.search(indicator, prompt, re.IGNORECASE):
                score += 1
                
        return min(score / len(specificity_indicators), 1.0)
    
    def _score_actionability(self, prompt: str) -> float:
        """Score how actionable the instructions are (0-1)."""
        action_verbs = [
            "evaluate",
            "identify",
            "analyze",
            "determine",
            "calculate",
            "assess",
            "classify",
            "generate",
            "provide"
        ]
        
        lower_prompt = prompt.lower()
        found = sum(1 for verb in action_verbs if verb in lower_prompt)
        
        return min(found / len(action_verbs), 1.0)
    
    def _score_consistency(self, prompt: str) -> float:
        """Score consistency guidelines (0-1)."""
        consistency_indicators = [
            "objective",
            "balanced",
            "systematic",
            "consistent",
            "avoid bias",
            "maintain",
            "throughout"
        ]
        
        lower_prompt = prompt.lower()
        found = sum(1 for indicator in consistency_indicators if indicator in lower_prompt)
        
        return min(found / 3, 1.0)  # Expect at least 3
    
    def generate_improvement_suggestions(self, metrics: PromptMetrics) -> List[str]:
        """Generate specific improvement suggestions based on metrics."""
        suggestions = []
        
        if metrics.instruction_clarity_score < 0.7:
            suggestions.append("Add clearer step-by-step instructions with numbered steps")
            
        if metrics.example_coverage < 0.7:
            suggestions.append("Include more concrete examples, especially full output examples")
            
        if metrics.output_specification_completeness < 0.8:
            suggestions.append("Specify all required output fields with descriptions")
            
        if metrics.role_definition_strength < 0.7:
            suggestions.append("Strengthen the role definition with specific expertise areas")
            
        if metrics.scoring_methodology_clarity < 0.8:
            suggestions.append("Clarify scoring calculations with explicit formulas")
            
        if metrics.framework_definitions < 3:
            suggestions.append("Define more evaluation frameworks (STAR-V, etc.)")
            
        if metrics.edge_case_handling < 0.6:
            suggestions.append("Add instructions for handling incomplete or missing data")
            
        if metrics.specificity_score < 0.7:
            suggestions.append("Use more specific language with concrete thresholds")
            
        if metrics.consistency_guidelines < 0.6:
            suggestions.append("Add guidelines for maintaining consistency across evaluations")
            
        if metrics.total_words < 500:
            suggestions.append("Expand prompt with more detailed instructions")
        elif metrics.total_words > 2000:
            suggestions.append("Consider condensing prompt while maintaining clarity")
            
        return suggestions
    
    def compare_prompts(self, prompt1: str, prompt2: str) -> Dict[str, Any]:
        """Compare two prompt versions."""
        metrics1 = self.analyze_prompt(prompt1)
        metrics2 = self.analyze_prompt(prompt2)
        
        comparison = {
            "prompt1_score": metrics1.overall_score(),
            "prompt2_score": metrics2.overall_score(),
            "improvement": metrics2.overall_score() - metrics1.overall_score(),
            "improved_dimensions": [],
            "degraded_dimensions": []
        }
        
        # Compare individual dimensions
        for attr in vars(metrics1):
            if attr == "total_words":
                continue
                
            val1 = getattr(metrics1, attr)
            val2 = getattr(metrics2, attr)
            
            if isinstance(val1, (int, float)):
                if val2 > val1 + 0.1:
                    comparison["improved_dimensions"].append(attr)
                elif val2 < val1 - 0.1:
                    comparison["degraded_dimensions"].append(attr)
                    
        return comparison