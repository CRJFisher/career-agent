---
id: task-6
title: Design job requirements YAML output schema
status: Done
assignee:
  - '@claude'
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Define the structured YAML format for extracted job requirements including must-haves, nice-to-haves, hard skills, soft skills, and experiences. This schema is critical for ensuring consistent and machine-readable output from the ExtractRequirementsNode. The format must distinguish between explicitly required items (must-haves) and advantageous but not mandatory items (nice-to-haves), with clear categorization of different requirement types.

## Acceptance Criteria

- [x] YAML schema for job_requirements defined with all fields
- [x] Schema includes role and company fields at top level
- [x] Schema separates must_haves and nice_to_haves sections
- [x] must_haves contains hard_skills soft_skills experiences subsections
- [x] nice_to_haves contains technologies interests subsections
- [x] Clear distinction between requirement categories
- [x] Example output format documented
- [x] Schema supports nested lists and descriptive strings

## Implementation Plan

1. Define top-level structure: job_requirements with role and company
2. Create must_haves section with three categories
3. Define hard_skills as list of technical requirements
4. Define soft_skills as list of interpersonal requirements
5. Define experiences as list of background requirements
6. Create nice_to_haves section with flexible categories
7. Document example with DeepMind Software Engineer role
8. Ensure schema is parseable and validates correctly

## Implementation Notes

- Created comprehensive job_requirements_schema.md documentation
- Schema structure already implemented in ExtractRequirementsNode (task-5)
- Refined schema with clear sections:
  - role_summary: title, company, location, type, level
  - hard_requirements: education, experience, technical_skills, certifications
  - soft_requirements: skills, traits, cultural_fit
  - nice_to_have: flexible categories for preferred qualifications
  - responsibilities: primary, secondary, leadership, collaboration
  - compensation_benefits: salary, benefits, perks, equity
- Created JSON Schema for programmatic validation
- Added _validate_with_schema() method to ExtractRequirementsNode
- Schema enforces required sections and validates data types
- Clear distinction between mandatory (hard_requirements) and optional (nice_to_have)
- Example shows DeepMind-style job with all sections populated
- Schema supports nested structures and lists as required
