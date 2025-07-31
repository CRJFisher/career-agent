---
id: task-21
title: Design suitability assessment prompt
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create the LLM prompt for the SuitabilityScoringNode that acts as a senior hiring manager to evaluate fit and generate unique value proposition. The prompt must guide the LLM to perform multiple assessment tasks in one call: calculate technical fit, assess cultural alignment, identify strengths and gaps, and most importantly formulate a unique value proposition by finding rare skill intersections (e.g., 'full-stack engineer with patented ML experience and proven track record of building user-loved developer tools').
## Acceptance Criteria

- [ ] Senior hiring manager role definition in prompt
- [ ] Technical fit scoring methodology (must-haves vs nice-to-haves)
- [ ] Weight system for requirement importance explained
- [ ] Cultural fit assessment criteria provided
- [ ] Instructions for identifying top strengths
- [ ] Gap significance evaluation guidelines
- [ ] Unique value proposition synthesis instructions
- [ ] Example of skill intersection identification included
- [ ] Prompt validation tests with sample inputs and expected outputs
- [ ] Tests verify prompt generates consistent scoring across multiple runs
- [ ] Tests ensure all required assessment components are addressed
- [ ] Tests validate example output format matches expected structure
- [ ] Edge case tests for incomplete or unclear requirement data

## Implementation Plan

1. Define role: 'You are a senior hiring manager evaluating a candidate'\n2. Explain technical fit scoring based on requirements met\n3. Add weighting system for must-haves vs nice-to-haves\n4. Include cultural fit assessment methodology\n5. Provide framework for strength identification\n6. Add guidelines for gap significance\n7. Emphasize unique value proposition creation\n8. Include example output format
