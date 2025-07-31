---
id: task-22
title: Implement ExperiencePrioritizationNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a pure Python node that scores and ranks all career experiences using weighted criteria. This node does NOT require LLM - it implements the user's explicit scoring framework with weights: relevance_to_role (40%), recency (20%), impact (20%), uniqueness (10%), growth (10%). The node iterates through every item in career_db and produces a ranked list that guides narrative prioritization. This algorithmic approach ensures consistent, explainable prioritization.
## Acceptance Criteria

- [ ] ExperiencePrioritizationNode class created with pure Python logic
- [ ] No LLM calls - implements deterministic scoring algorithm
- [ ] Weighted scoring: relevance 40% recency 20% impact 20% uniqueness 10% growth 10%
- [ ] Processes all professional_experience entries from career_db
- [ ] Processes all projects entries from career_db
- [ ] Calculates composite score for each experience
- [ ] Returns sorted list by score (highest first)
- [ ] Scoring methodology documented in code
- [ ] Unit tests for each scoring criterion function
- [ ] Tests verify weighted calculation accuracy (40/20/20/10/10)
- [ ] Tests validate proper handling of all career_db entries
- [ ] Tests ensure correct sorting by composite score
- [ ] Edge case tests for missing dates or incomplete experience data
- [ ] Tests verify scoring consistency and deterministic results
- [ ] Performance tests for large career databases

## Implementation Plan

1. Create ExperiencePrioritizationNode class\n2. Implement prep() to load career_db and requirements\n3. Define scoring functions for each criterion\n4. Implement relevance scoring against job requirements\n5. Calculate recency score based on dates\n6. Extract impact score from quantified achievements\n7. Assess uniqueness and growth demonstration\n8. Sort experiences by composite score
