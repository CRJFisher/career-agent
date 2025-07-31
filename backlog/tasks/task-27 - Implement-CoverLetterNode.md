---
id: task-27
title: Implement CoverLetterNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a node that generates a compelling cover letter following the user-specified 5-part structure: Hook, Value Proposition, Evidence, Company Fit, Call to Action. The node uses narrative strategy, company research, and suitability assessment to create a personalized, authentic letter. Each section has specific requirements - Hook addresses company need, Value Proposition states unique value, Evidence provides CAR stories, Company Fit shows research, Call to Action is confident and clear.
## Acceptance Criteria

- [ ] CoverLetterNode class created following Node lifecycle
- [ ] 5-part structure template strictly followed
- [ ] Hook directly addresses company need/goal from research
- [ ] Value proposition uses unique_value_proposition from assessment
- [ ] Evidence section incorporates 2-3 CAR format stories
- [ ] Company fit demonstrates deep research understanding
- [ ] Call to action is confident and specific
- [ ] Authentic personalized tone throughout letter

## Implementation Plan

1. Create CoverLetterNode class with Node interface\n2. Design cover letter prompt with 5-part template\n3. Map Hook to company mission/goal from research\n4. Use unique_value_proposition for section 2\n5. Include evidence_stories from narrative strategy\n6. Reference company culture and values for fit\n7. Create strong call to action conclusion\n8. Output text to shared['cover_letter_text']
