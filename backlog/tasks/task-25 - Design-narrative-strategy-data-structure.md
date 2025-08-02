---
id: task-25
title: Design narrative strategy data structure
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Define the structure for the narrative strategy output including career arc, key messages, must-tell experiences, differentiators, and evidence stories. This data structure serves as the blueprint for material generation, containing both strategic decisions (which experiences to highlight) and tactical content (specific stories and messages). The structure must support the 5-part cover letter format and guide CV generation.

## Acceptance Criteria

- [x] Narrative strategy schema with all components defined
- [x] Career arc structure with past/present/future components
- [x] Key messages array with 3 concise powerful statements
- [x] Must-tell experiences list with rationale for selection
- [x] Differentiators list highlighting unique value
- [x] Evidence stories in detailed CAR format
- [x] Integration points with CV and cover letter generation
- [x] Example narrative strategy with populated data
- [x] Data structure validation schema defined and tested
- [x] Tests verify all required components are present
- [x] Tests validate proper nesting and field types
- [x] Tests ensure integration compatibility with generation flows
- [x] Validation tests for CAR story format requirements
- [x] Tests verify example data passes all validation rules

## Implementation Plan

1. Define top-level narrative_strategy structure
2. Create career_arc object with three time phases
3. Define key_messages as array of strings
4. Structure must_tell_experiences with experience and reason
5. Structure differentiators with uniqueness explanation
6. Define evidence_stories with challenge/action/result
7. Document how each component maps to materials
8. Create comprehensive example

## Implementation Notes & Findings

### Schema Design

Created comprehensive YAML schema (`schemas/narrative_strategy_schema.yaml`) with:
- **5 required top-level fields**: must_tell_experiences, differentiators, career_arc, key_messages, evidence_stories
- **Strict constraints**: 2-3 must-tell experiences, 1-2 differentiators, exactly 3 key messages, 0-2 evidence stories
- **Detailed substructures**: CAR format for stories, past/present/future for career arc
- **Field validation**: Min/max lengths for all text fields to ensure quality

### Validation Implementation

Built robust Python validator (`utils/narrative_strategy_validator.py`) with:
- **Field-level validation**: Type checking, length constraints, required fields
- **Nested validation**: Validates substructures like key_points arrays
- **Integration checks**: Ensures compatibility with CV/cover letter generation
- **CLI interface**: Can validate YAML files directly from command line
- **Clear error messages**: Specific feedback on what needs fixing

### Example Creation

Developed comprehensive example (`examples/narrative_strategy_example.yaml`) showing:
- **Senior Platform Engineer** narrative with all fields populated
- **3 must-tell experiences** with clear selection rationale
- **2 differentiators** highlighting rare skill combinations
- **Complete career arc** with company mention in future
- **2 detailed CAR stories** with quantified results

### Integration Documentation

Created integration guide (`docs/narrative_strategy_integration.md`) explaining:
- **Cover letter mapping**: Each component maps to specific paragraphs
- **CV section mapping**: How narrative drives CV structure
- **Priority system**: Must-tell experiences featured prominently
- **Consistency requirements**: Key messages threaded throughout

### Testing Coverage

Comprehensive test suite (15 tests) covering:
- **Valid structure validation**: Ensures good data passes
- **Constraint enforcement**: Min/max items, field lengths
- **Type validation**: Lists vs dicts, strings vs other types
- **Integration compatibility**: Checks for generation requirements
- **Edge cases**: Empty stories, minimal valid structure
- **YAML file handling**: Both wrapped and unwrapped formats

### Key Design Decisions

1. **Exactly 3 Key Messages**: Forces focus and consistency
2. **2-3 Must-Tell Experiences**: Balance between depth and brevity
3. **CAR Format Stories**: Standard behavioral interview preparation
4. **Career Arc Structure**: Past/present/future creates compelling narrative
5. **Integration Compatibility**: Separate validation ensures generation success

### Data Flow

1. **Input**: Prioritized experiences + suitability assessment
2. **Processing**: NarrativeStrategyNode synthesizes strategy
3. **Validation**: Ensures all required fields present and valid
4. **Storage**: Saved to checkpoint for user review/edit
5. **Consumption**: CVGenerationNode and CoverLetterNode use strategy

### Field Purposes

- **must_tell_experiences**: Core evidence for value proposition
- **differentiators**: Unique positioning vs other candidates
- **career_arc**: Coherent progression story
- **key_messages**: Consistent themes across materials
- **evidence_stories**: Detailed behavioral examples

### Integration Points

The narrative strategy serves as the bridge between:
- **Analysis outputs** (requirements mapping, gaps, suitability)
- **Document generation** (CV, cover letter)
- **User customization** (checkpoint editing)
- **Consistency enforcement** (same messages everywhere)

This data structure successfully provides both strategic guidance and tactical content for generating compelling application materials.
