---
id: task-19
title: Implement SuitabilityScoringNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a node that performs holistic evaluation of job fit including technical fit score, cultural fit score, strengths, gaps, and unique value proposition. This single powerful node takes requirement mappings and gaps as input and uses LLM acting as senior hiring manager to perform comprehensive assessment. The unique value proposition is critical - identifying rare and powerful intersections of skills that differentiate the candidate.

## Acceptance Criteria

- [ ] SuitabilityScoringNode class created following Node lifecycle
- [ ] LLM prompt for senior hiring manager perspective implemented
- [ ] Technical fit scoring algorithm (0-100) based on requirements met
- [ ] Cultural fit scoring using company research insights
- [ ] Identifies top 3-5 compelling strengths from mapping
- [ ] Summarizes most significant gaps honestly
- [ ] Synthesizes unique value proposition from skill intersections
- [ ] Complete suitability_assessment dict saved to shared store
- [ ] Unit tests for scoring algorithm accuracy and consistency
- [ ] Tests verify technical fit scoring logic (0-100 range)
- [ ] Tests validate cultural fit assessment generation
- [ ] Tests ensure strengths and gaps identification logic
- [ ] Mock LLM tests for prompt handling and response parsing
- [ ] Tests verify complete assessment data structure
- [ ] Edge case tests for missing or incomplete input data

## Implementation Plan

1. Create SuitabilityScoringNode with Node interface
2. Design comprehensive scoring prompt
3. Include technical fit calculation methodology
4. Add cultural fit assessment based on research
5. Extract strengths from HIGH-scored mappings
6. Identify critical gaps from analysis
7. Generate unique value proposition statement
8. Output complete assessment dictionary
