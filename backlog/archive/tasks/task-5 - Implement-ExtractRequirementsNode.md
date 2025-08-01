---
id: task-5
title: Implement ExtractRequirementsNode
status: Done
assignee:
  - '@claude'
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a PocketFlow node that extracts structured job requirements from unstructured job descriptions using LLM with structured output pattern. This implements Phase 1 of the job application agent, transforming free-form text into the specified YAML format. The node leverages sophisticated prompting techniques to compel the LLM to generate responses that strictly adhere to the predefined schema. This is a perfect application of the Structured Output design pattern as explicitly listed in PocketFlow tutorials.

## Acceptance Criteria

- [x] ExtractRequirementsNode class created in nodes.py
- [x] Follows PocketFlow Node lifecycle (prep/exec/post)
- [x] prep method reads job_spec_text from shared['job_spec_text']
- [x] exec method calls LLM with meticulously engineered prompt
- [x] Prompt includes role definition task instruction and one-shot example
- [x] post method parses YAML output and saves to shared['job_requirements_structured']
- [x] Error handling for malformed LLM responses
- [x] Retry logic for failed extractions

## Implementation Plan

1. Create ExtractRequirementsNode class inheriting from PocketFlow Node
2. Implement prep() to read job description from shared store
3. Design exec() with LLM call using structured output prompt
4. Include system prompt: 'You are an expert HR analyst and senior technical recruiter'
5. Add one-shot example from DeepMind job in prompt
6. Implement post() to parse YAML and handle errors
7. Add retry mechanism for malformed responses
8. Return appropriate action string for flow control

## Implementation Notes

- Created ExtractRequirementsNode inheriting from base Node class
- Implemented async execute() method following PocketFlow pattern
- Created comprehensive LLM wrapper utility first (partial task-32 implementation)
- LLM wrapper supports OpenAI and Anthropic with retry logic using tenacity
- Added call_llm_structured() method for YAML/JSON parsing with retries
- ExtractRequirementsNode uses system prompt defining HR analyst role
- Detailed one-shot example shows expected YAML structure for DeepMind-style job
- YAML structure includes:
  - role_summary: title, company, location, type, level
  - hard_requirements: education, experience, technical_skills
  - soft_requirements: skills, traits
  - nice_to_have: certifications, experience, skills  
  - responsibilities: primary, secondary
  - compensation_benefits: salary, benefits, perks
- Validation ensures required sections and fields are present
- Error handling returns status and error message in store
- Temperature set to 0.3 for consistent structured output
- Comprehensive unit tests with mocking for LLM calls
- Tests cover success cases, validation errors, and LLM failures
