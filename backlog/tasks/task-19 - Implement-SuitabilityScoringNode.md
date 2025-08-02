---
id: task-19
title: Implement SuitabilityScoringNode
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create a node that performs holistic evaluation of job fit including technical fit score, cultural fit score, strengths, gaps, and unique value proposition. This single powerful node takes requirement mappings and gaps as input and uses LLM acting as senior hiring manager to perform comprehensive assessment. The unique value proposition is critical - identifying rare and powerful intersections of skills that differentiate the candidate.

## Acceptance Criteria

- [x] SuitabilityScoringNode class created following Node lifecycle
- [x] LLM prompt for senior hiring manager perspective implemented
- [x] Technical fit scoring algorithm (0-100) based on requirements met
- [x] Cultural fit scoring using company research insights
- [x] Identifies top 3-5 compelling strengths from mapping
- [x] Summarizes most significant gaps honestly
- [x] Synthesizes unique value proposition from skill intersections
- [x] Complete suitability_assessment dict saved to shared store
- [x] Unit tests for scoring algorithm accuracy and consistency
- [x] Tests verify technical fit scoring logic (0-100 range)
- [x] Tests validate cultural fit assessment generation
- [x] Tests ensure strengths and gaps identification logic
- [x] Mock LLM tests for prompt handling and response parsing
- [x] Tests verify complete assessment data structure
- [x] Edge case tests for missing or incomplete input data

## Implementation Plan

1. Create SuitabilityScoringNode with Node interface
2. Design comprehensive scoring prompt
3. Include technical fit calculation methodology
4. Add cultural fit assessment based on research
5. Extract strengths from HIGH-scored mappings
6. Identify critical gaps from analysis
7. Generate unique value proposition statement
8. Output complete assessment dictionary

## Implementation Notes & Findings

### Technical Fit Scoring Algorithm

The scoring system was designed to be transparent and predictable:

1. **Score Distribution**:
   - Required skills: 60% (most important)
   - Preferred skills: 20% (nice to have)
   - Other categories (experience/education): 20%

2. **Strength Mapping**:
   - HIGH strength: 100% of allocated points
   - MEDIUM strength: 60% of allocated points
   - LOW strength: 30% of allocated points
   - Missing/Gap: 0% of allocated points

3. **Key Design Decision**: Used a deterministic calculation for technical fit rather than LLM assessment to ensure consistency and explainability.

### LLM Prompt Design

The prompt adopts a senior hiring manager perspective with structured sections:

1. **Context Section**: Technical fit score, requirement mapping summary, gaps
2. **Company Context**: Extracted from company research for cultural alignment
3. **Task Instructions**: Clear focus areas for the LLM to evaluate

### Unique Value Proposition

This was the most challenging aspect - instructing the LLM to identify "rare intersections of skills" that make a candidate special. The prompt specifically asks for combinations that are hard to find in the market.

### Error Handling Strategy

1. **Graceful Degradation**: If LLM fails, return a minimal but valid assessment
2. **Field Validation**: Check for all required fields and provide sensible defaults
3. **Logging**: Comprehensive logging of scores and counts for debugging

### Testing Insights

1. **Score Calculation Tests**: Initially failed due to misunderstanding of the scoring math. Each requirement gets equal weight within its category.
2. **Mock Complexity**: Need to mock both the LLM wrapper and its responses
3. **Data Structure**: The assessment structure with 6 key fields provides a comprehensive view

### Integration Considerations

- The node expects `requirement_mapping_final` from GapAnalysisNode (not raw mappings)
- Company research is optional but significantly impacts cultural fit assessment
- The technical fit score is objective while cultural fit relies on LLM interpretation
