---
id: task-7
title: Create requirements extraction prompt engineering
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Develop and optimize the LLM prompt for extracting structured job requirements. The prompt must use one-shot prompting technique with a perfect example to leverage the LLM's in-context learning capabilities. Modern LLM APIs offer json_schema response formats, but a well-crafted prompt remains essential for semantic accuracy. The prompt quality directly impacts the reliability of structured output extraction.
## Acceptance Criteria

- [ ] System prompt defining HR analyst role created
- [ ] Task instruction for requirement categorization written
- [ ] Clear distinction between must-haves and nice-to-haves explained
- [ ] YAML format specification with strict output rules
- [ ] One-shot example using DeepMind Software Engineer job
- [ ] Prompt instructs NO text outside YAML block
- [ ] Prompt tested for reliability with multiple job descriptions
- [ ] Handles various job description formats and styles

## Implementation Plan

1. Write role definition: 'You are an expert HR analyst and senior technical recruiter'\n2. Create task instruction explaining requirement analysis goals\n3. Define categorization rules for hard_skills, soft_skills, experiences\n4. Add format specification requiring ONLY valid YAML output\n5. Include complete one-shot example with DeepMind job\n6. Add explicit instruction to exclude any non-YAML content\n7. Test prompt with diverse job descriptions\n8. Iterate based on output quality and adherence
