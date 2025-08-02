"""
Tests for prompt effectiveness analyzer.

Validates that our suitability assessment prompt meets quality standards.
"""

import pytest
from pathlib import Path

from utils.prompt_effectiveness_analyzer import (
    PromptEffectivenessAnalyzer,
    PromptMetrics
)


class TestPromptEffectiveness:
    """Test suite for prompt effectiveness analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return PromptEffectivenessAnalyzer()
    
    @pytest.fixture  
    def prompt_content(self):
        """Load actual prompt content."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "suitability_assessment_prompt.md"
        with open(prompt_path, "r") as f:
            return f.read()
    
    def test_analyze_actual_prompt(self, analyzer, prompt_content):
        """Test analysis of our actual suitability assessment prompt."""
        metrics = analyzer.analyze_prompt(prompt_content)
        
        # Check overall quality
        assert metrics.overall_score() >= 0.7, \
            f"Prompt quality score {metrics.overall_score():.2f} below threshold"
        
        # Check specific dimensions
        assert metrics.instruction_clarity_score >= 0.7
        assert metrics.example_coverage >= 0.7
        assert metrics.output_specification_completeness >= 0.8
        assert metrics.role_definition_strength >= 0.7
        assert metrics.scoring_methodology_clarity >= 0.8
        assert metrics.framework_definitions >= 3
        assert metrics.specificity_score >= 0.6
        assert metrics.actionability_score >= 0.7
    
    def test_improvement_suggestions(self, analyzer, prompt_content):
        """Test that analyzer provides actionable improvement suggestions."""
        metrics = analyzer.analyze_prompt(prompt_content)
        suggestions = analyzer.generate_improvement_suggestions(metrics)
        
        # Should have concrete suggestions if score < 1.0
        if metrics.overall_score() < 1.0:
            assert len(suggestions) > 0
            # Suggestions should be actionable
            for suggestion in suggestions:
                assert len(suggestion) > 20  # Non-trivial suggestion
                assert any(action in suggestion.lower() 
                          for action in ["add", "include", "specify", "define", "expand"])
    
    def test_metrics_calculation(self, analyzer):
        """Test metrics calculation on minimal prompt."""
        minimal_prompt = """
        You are a hiring manager. Evaluate this candidate.
        
        Output format:
        - score: number
        - recommendation: text
        """
        
        metrics = analyzer.analyze_prompt(minimal_prompt)
        
        # Minimal prompt should score low
        assert metrics.overall_score() < 0.5
        assert metrics.example_coverage < 0.3
        assert metrics.framework_definitions == 0
        assert metrics.scoring_methodology_clarity < 0.3
    
    def test_comprehensive_prompt_scores_high(self, analyzer):
        """Test that comprehensive prompt scores well."""
        comprehensive_prompt = """
        You are a senior hiring manager with 15 years of experience evaluating technical talent.
        
        ## Your Task
        Evaluate the candidate systematically using the following methodology.
        
        ## Scoring Methodology
        Technical skills are scored as follows:
        - HIGH strength = 100% of allocated points
        - MEDIUM strength = 60% of allocated points
        - LOW strength = 30% of allocated points
        - Missing = 0% of allocated points
        
        ## Evaluation Framework
        Use the STAR-V method for identifying strengths:
        - Specific: Concrete examples
        - Transferable: Applies to role
        - Amplified: Enhanced by other skills
        - Rare: Uncommon in market
        - Valuable: Business impact
        
        ## Output Format
        Generate output in YAML format:
        ```yaml
        technical_score: <0-100>
        cultural_score: <0-100>
        strengths:
          - description: <specific strength>
            evidence: <proof>
        recommendation: <yes/no/maybe>
        ```
        
        ## Example
        For a backend engineer with Python expertise:
        ```yaml
        technical_score: 85
        cultural_score: 90
        strengths:
          - description: Deep Python optimization experience
            evidence: Reduced latency by 10x at previous company
        recommendation: yes
        ```
        
        ## Edge Cases
        If information is incomplete, acknowledge limitations and provide caveated assessment.
        """
        
        metrics = analyzer.analyze_prompt(comprehensive_prompt)
        
        # Comprehensive prompt should score high
        assert metrics.overall_score() >= 0.7
        assert metrics.instruction_clarity_score >= 0.7
        assert metrics.example_coverage >= 0.7
        assert metrics.output_specification_completeness >= 0.7
        assert metrics.framework_definitions >= 1
        assert metrics.edge_case_handling >= 0.6
    
    def test_prompt_comparison(self, analyzer, prompt_content):
        """Test comparing prompt versions."""
        # Create simplified version
        simplified = prompt_content[:1000]  # Just first part
        
        comparison = analyzer.compare_prompts(simplified, prompt_content)
        
        # Full prompt should score higher
        assert comparison["prompt2_score"] > comparison["prompt1_score"]
        assert comparison["improvement"] > 0
        assert len(comparison["improved_dimensions"]) > 0
    
    def test_all_expected_sections_present(self, analyzer, prompt_content):
        """Test that all expected sections are in the prompt."""
        lower_content = prompt_content.lower()
        
        for section in analyzer.EXPECTED_SECTIONS:
            assert section in lower_content, f"Missing expected section: {section}"
    
    def test_output_fields_specified(self, analyzer, prompt_content):
        """Test that all required output fields are specified."""
        lower_content = prompt_content.lower()
        
        for field in analyzer.REQUIRED_OUTPUT_FIELDS:
            assert field in lower_content, f"Missing output field specification: {field}"
    
    def test_word_count_reasonable(self, analyzer, prompt_content):
        """Test prompt length is reasonable."""
        metrics = analyzer.analyze_prompt(prompt_content)
        
        # Should be comprehensive but not overwhelming
        assert 500 <= metrics.total_words <= 2500, \
            f"Prompt length {metrics.total_words} words outside reasonable range"
    
    def test_actionability_high(self, analyzer, prompt_content):
        """Test that prompt contains actionable instructions."""
        metrics = analyzer.analyze_prompt(prompt_content)
        
        assert metrics.actionability_score >= 0.6, \
            "Prompt should contain more action verbs and clear directives"
    
    def test_consistency_guidelines_present(self, analyzer, prompt_content):
        """Test that prompt includes consistency guidelines."""
        metrics = analyzer.analyze_prompt(prompt_content)
        
        assert metrics.consistency_guidelines >= 0.5, \
            "Prompt should include more guidance on maintaining consistency"