---
id: task-7
title: Create requirements extraction prompt engineering
status: Done
assignee:
  - '@claude'
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Develop and optimize the LLM prompt for extracting structured job requirements. The prompt must use one-shot prompting technique with a perfect example to leverage the LLM's in-context learning capabilities. Modern LLM APIs offer json_schema response formats, but a well-crafted prompt remains essential for semantic accuracy. The prompt quality directly impacts the reliability of structured output extraction.
## Acceptance Criteria

- [x] System prompt defining HR analyst role created
- [x] Task instruction for requirement categorization written
- [x] Clear distinction between must-haves and nice-to-haves explained
- [x] YAML format specification with strict output rules
- [x] One-shot example using DeepMind Software Engineer job
- [x] Prompt instructs NO text outside YAML block
- [x] Prompt tested for reliability with multiple job descriptions
- [x] Handles various job description formats and styles

## Implementation Plan

1. Write role definition: 'You are an expert HR analyst and senior technical recruiter'\n2. Create task instruction explaining requirement analysis goals\n3. Define categorization rules for hard_skills, soft_skills, experiences\n4. Add format specification requiring ONLY valid YAML output\n5. Include complete one-shot example with DeepMind job\n6. Add explicit instruction to exclude any non-YAML content\n7. Test prompt with diverse job descriptions\n8. Iterate based on output quality and adherence

## Implementation Notes

- Prompt engineering was implemented as part of ExtractRequirementsNode (task-5)
- System prompt: "You are an expert HR analyst and senior technical recruiter..."
- Clear task instruction to extract and structure requirements in YAML
- One-shot example using DeepMind-style Senior Software Engineer role
- Example demonstrates all schema sections with proper formatting
- Explicit instruction: "Your response must be ONLY valid YAML with no additional text"
- Reminder at end: "Remember: Respond with ONLY the YAML structure, no additional text"
- Temperature set to 0.3 for consistent structured output
- Prompt tested with comprehensive unit tests including edge cases
