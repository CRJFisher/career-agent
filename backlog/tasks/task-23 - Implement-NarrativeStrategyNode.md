---
id: task-23
title: Implement NarrativeStrategyNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create an LLM-driven node that synthesizes a complete narrative strategy including must-tell experiences, differentiators, career arc, key messages, and evidence stories. This sophisticated node acts as an expert career coach, taking the prioritized experience list and suitability assessment to craft a compelling application narrative. The node selects top experiences, formulates career progression story, and creates detailed CAR (Challenge, Action, Result) format evidence stories.
## Acceptance Criteria

- [ ] NarrativeStrategyNode class created following Node lifecycle
- [ ] Career storyteller prompt for strategic synthesis
- [ ] Selects top 2-3 must-tell experiences from ranked list
- [ ] Identifies 1-2 unique differentiator experiences
- [ ] Formulates career arc narrative (past present future)
- [ ] Defines 3 concise key messages for application
- [ ] Creates 1-2 detailed CAR format evidence stories
- [ ] Complete narrative_strategy dict saved to shared store
- [ ] Unit tests for node initialization and lifecycle methods
- [ ] Tests verify experience selection logic (top 2-3 must-tells)
- [ ] Tests validate differentiator identification accuracy
- [ ] Tests ensure career arc narrative coherence
- [ ] Tests verify key message generation quality and count
- [ ] Tests validate CAR story format and completeness
- [ ] Mock LLM tests for prompt handling and response parsing

## Implementation Plan

1. Create NarrativeStrategyNode class with Node interface\n2. Design expert career coach prompt\n3. Implement experience selection logic (top 2-3 must-tells)\n4. Add differentiator identification (1-2 unique experiences)\n5. Include career arc formulation instructions\n6. Define key message generation requirements\n7. Add CAR story format template and examples\n8. Output comprehensive narrative strategy
