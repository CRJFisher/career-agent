---
id: task-6
title: Design job requirements YAML output schema
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Define the structured YAML format for extracted job requirements including must-haves, nice-to-haves, hard skills, soft skills, and experiences. This schema is critical for ensuring consistent and machine-readable output from the ExtractRequirementsNode. The format must distinguish between explicitly required items (must-haves) and advantageous but not mandatory items (nice-to-haves), with clear categorization of different requirement types.
## Acceptance Criteria

- [ ] YAML schema for job_requirements defined with all fields
- [ ] Schema includes role and company fields at top level
- [ ] Schema separates must_haves and nice_to_haves sections
- [ ] must_haves contains hard_skills soft_skills experiences subsections
- [ ] nice_to_haves contains technologies interests subsections
- [ ] Clear distinction between requirement categories
- [ ] Example output format documented
- [ ] Schema supports nested lists and descriptive strings

## Implementation Plan

1. Define top-level structure: job_requirements with role and company\n2. Create must_haves section with three categories\n3. Define hard_skills as list of technical requirements\n4. Define soft_skills as list of interpersonal requirements\n5. Define experiences as list of background requirements\n6. Create nice_to_haves section with flexible categories\n7. Document example with DeepMind Software Engineer role\n8. Ensure schema is parseable and validates correctly
