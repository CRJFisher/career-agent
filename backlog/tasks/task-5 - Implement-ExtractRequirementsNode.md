---
id: task-5
title: Implement ExtractRequirementsNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a PocketFlow node that extracts structured job requirements from unstructured job descriptions using LLM with structured output pattern. This implements Phase 1 of the job application agent, transforming free-form text into the specified YAML format. The node leverages sophisticated prompting techniques to compel the LLM to generate responses that strictly adhere to the predefined schema. This is a perfect application of the Structured Output design pattern as explicitly listed in PocketFlow tutorials.
## Acceptance Criteria

- [ ] ExtractRequirementsNode class created in nodes.py
- [ ] Follows PocketFlow Node lifecycle (prep/exec/post)
- [ ] prep method reads job_spec_text from shared['job_spec_text']
- [ ] exec method calls LLM with meticulously engineered prompt
- [ ] Prompt includes role definition task instruction and one-shot example
- [ ] post method parses YAML output and saves to shared['job_requirements_structured']
- [ ] Error handling for malformed LLM responses
- [ ] Retry logic for failed extractions

## Implementation Plan

1. Create ExtractRequirementsNode class inheriting from PocketFlow Node\n2. Implement prep() to read job description from shared store\n3. Design exec() with LLM call using structured output prompt\n4. Include system prompt: 'You are an expert HR analyst and senior technical recruiter'\n5. Add one-shot example from DeepMind job in prompt\n6. Implement post() to parse YAML and handle errors\n7. Add retry mechanism for malformed responses\n8. Return appropriate action string for flow control
