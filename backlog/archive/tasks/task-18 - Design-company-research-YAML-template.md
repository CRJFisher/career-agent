---
id: task-18
title: Design company research YAML template
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Define the structured format for company research output including mission, team scope, strategic importance, and culture fields. This YAML template guides the research agent's information gathering and ensures comprehensive company understanding. The template must capture both factual information (mission, team details) and analytical insights (strategic importance, culture). This structured output feeds into later phases for tailored application materials.

## Acceptance Criteria

- [x] Company research YAML schema with nested structure defined
- [x] Top level: company_research with company name as key
- [x] Required fields: mission team_scope strategic_importance culture
- [x] Each field has clear purpose and expected content type
- [x] Mission captures company's stated purpose and goals
- [x] Team_scope describes specific team/role context
- [x] Strategic_importance analyzes role's impact on company
- [x] Culture summarizes work environment and values
- [x] YAML schema validation rules defined and tested
- [x] Tests verify template structure matches expected format
- [x] Validation tests for required field presence
- [x] Tests ensure field content types are correctly specified
- [x] Example template passes all validation requirements

## Implementation Plan

1. Define company_research as top-level key
2. Use company name as nested key for multi-company support
3. Define mission field for company purpose/goals
4. Define team_scope for specific team information
5. Define strategic_importance for role analysis
6. Define culture for work environment details
7. Document expected content for each field
8. Create example with populated research data

## Implementation Notes & Findings

### Schema Design Decisions

1. **Structure Simplification**: Instead of using company name as a nested key, kept a flat structure with `company_research` as the top-level key. This simplifies validation and usage since we typically research one company at a time.

2. **Field Organization**: Organized fields into three categories:
   - **Core Required Fields**: mission, team_scope, strategic_importance, culture
   - **Extended Optional Fields**: technology_stack_practices, recent_developments, market_position_growth
   - **Nested Required Fields**: Specific subfields within objects like team_name, size, responsibilities

3. **Validation Constraints**:
   - **String Length**: Mission (50-500 chars), business_impact (min 50), growth_trajectory (min 30)
   - **List Sizes**: responsibilities (min 2), values (2-6 items)
   - **Enums**: remote_policy must be one of ["Remote-first", "Hybrid", "Office-first", "Flexible"]

### Implementation Architecture

Created three complementary components:

1. **YAML Schema Documentation** (`schemas/company_research_schema.yaml`):
   - Comprehensive schema definition with field descriptions
   - Examples for each field type
   - Complete example instance

2. **Python Validator** (`utils/company_research_validator.py`):
   - Programmatic validation logic
   - Type checking, length validation, enum constraints
   - Nested structure validation
   - Helper methods for creating minimal valid structures

3. **Validation CLI Tool** (`utils/validate_research.py`):
   - Command-line interface for validating YAML files
   - Verbose error reporting
   - Clean success/failure indicators

### Key Technical Insights

1. **Recursive Validation**: Implemented nested validation that applies constraints to fields at any depth in the structure.

2. **Graceful Optionality**: Optional fields can be completely omitted without errors, but if present must meet constraints.

3. **Practical Constraints**: Set reasonable minimums (e.g., 50 chars for mission) to ensure meaningful content while not being overly restrictive.

4. **Schema Evolution**: Structure supports adding new optional fields without breaking existing data.

### Integration with CompanyResearchAgent

The schema aligns perfectly with the existing implementation in `CompanyResearchAgent`:
- The flow already initializes the exact structure we formalized
- Tool nodes populate these fields through web research
- SynthesizeInfoNode can validate against our schema before saving

### Testing Strategy

Created comprehensive test suite covering:
- Minimal valid structures
- Complete structures with all optional fields
- Missing required fields detection
- Type validation
- Length and size constraints
- Enum validation
- Nested structure validation
- YAML file validation

### Future Enhancements

1. **JSON Schema Export**: Could generate standard JSON Schema from our validator
2. **Auto-correction**: Add methods to fix common validation errors
3. **Partial Validation**: Support validating incomplete research during agent iterations
4. **Field Importance Scoring**: Add weights to fields for prioritizing research
