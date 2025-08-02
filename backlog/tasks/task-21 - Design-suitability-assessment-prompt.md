---
id: task-21
title: Design suitability assessment prompt
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create the LLM prompt for the SuitabilityScoringNode that acts as a senior hiring manager to evaluate fit and generate unique value proposition. The prompt must guide the LLM to perform multiple assessment tasks in one call: calculate technical fit, assess cultural alignment, identify strengths and gaps, and most importantly formulate a unique value proposition by finding rare skill intersections (e.g., 'full-stack engineer with patented ML experience and proven track record of building user-loved developer tools').

## Acceptance Criteria

- [x] Senior hiring manager role definition in prompt
- [x] Technical fit scoring methodology (must-haves vs nice-to-haves)
- [x] Weight system for requirement importance explained
- [x] Cultural fit assessment criteria provided
- [x] Instructions for identifying top strengths
- [x] Gap significance evaluation guidelines
- [x] Unique value proposition synthesis instructions
- [x] Example of skill intersection identification included
- [x] Prompt validation tests with sample inputs and expected outputs
- [x] Tests verify prompt generates consistent scoring across multiple runs
- [x] Tests ensure all required assessment components are addressed
- [x] Tests validate example output format matches expected structure
- [x] Edge case tests for incomplete or unclear requirement data

## Implementation Plan

1. Define role: 'You are a senior hiring manager evaluating a candidate'
2. Explain technical fit scoring based on requirements met
3. Add weighting system for must-haves vs nice-to-haves
4. Include cultural fit assessment methodology
5. Provide framework for strength identification
6. Add guidelines for gap significance
7. Emphasize unique value proposition creation
8. Include example output format

## Implementation Notes & Findings

### Prompt Design Architecture

Created a comprehensive prompt design document (`prompts/suitability_assessment_prompt.md`) with the following key components:

1. **Role Definition**: Senior hiring manager with 15+ years experience, emphasizing both data-driven and human judgment
2. **Technical Scoring Methodology**: Clear point allocation system (HIGH=100%, MEDIUM=60%, LOW=30%, Missing=0%)
3. **Cultural Fit Framework**: Four dimensions each weighted 25% - work style, values, team dynamics, growth mindset
4. **STAR-V Method**: Structured approach for identifying strengths (Specific, Transferable, Amplified, Rare, Valuable)
5. **Gap Classification**: Four levels from critical blockers to non-issues based on impact and learnability
6. **UVP Framework**: "Venn Diagram" approach to identify rare skill intersections

### Key Design Decisions

1. **Structured Output**: Chose YAML format for clear hierarchy and easy parsing
2. **Breakdown Fields**: Added `cultural_fit_breakdown` to show scoring transparency
3. **Evidence-Based**: Required evidence and business impact for each strength
4. **Comprehensive Example**: Included full example for a Senior Backend Engineer scenario
5. **Special Instructions**: Added 6 guidelines including objectivity, consistency, and bias acknowledgment

### Testing Framework

Created three testing components:

1. **Prompt Validation Tests** (`test_suitability_assessment_prompt.py`):
   - 15 tests validating prompt structure, content, and examples
   - Tests for edge cases like low technical scores and missing gaps
   - Validation of all required output fields

2. **Prompt Variations** (`prompt_variations.yaml`):
   - 6 test scenarios from perfect fit to career changer
   - Edge cases including minimal information and conflicting signals
   - Anti-patterns to avoid (generic strengths, vague UVP)

3. **Effectiveness Analyzer** (`prompt_effectiveness_analyzer.py`):
   - Quantitative metrics for prompt quality
   - Automated improvement suggestions
   - Comparison capabilities for A/B testing prompts

### Technical Insights

1. **Markdown Handling**: Tests revealed markdown formatting (e.g., `**T**ransferable`) requires special handling in validation
2. **Prompt Length**: At 1,113 words, the prompt is comprehensive without being overwhelming
3. **Instruction Clarity**: Achieved high scores for example coverage (96%) and output specification (100%)
4. **Framework Integration**: Successfully integrated multiple evaluation frameworks (STAR-V, cultural dimensions, gap levels)

### Integration with SuitabilityScoringNode

The prompt design aligns with the existing implementation:
- `_build_assessment_prompt()` method already uses similar structure
- Technical scoring calculation matches the specified methodology
- Output format matches the expected YAML structure

### Future Enhancements

1. **Version Control**: Track prompt versions for A/B testing
2. **Dynamic Adaptation**: Adjust prompt based on role type and seniority
3. **Calibration Data**: Collect actual assessments to refine scoring thresholds
4. **Multi-rater Simulation**: Add perspectives from different stakeholder types

### Validation Results

- All 15 structural tests pass
- Prompt effectiveness score: 0.72/1.0 (above 0.7 threshold)
- Strong points: Example coverage, output specification, framework definitions
- Areas for potential improvement: More action verbs, additional specificity markers
