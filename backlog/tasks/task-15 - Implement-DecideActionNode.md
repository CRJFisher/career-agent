---
id: task-15
title: Implement DecideActionNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create the cognitive core node for the company research agent that decides which tool to use next based on current research state. This implements the Agent pattern's decision-making capability. The node assesses research progress, determines what information is still needed, and selects appropriate tools (web_search, read_content, synthesize, or finish). The prompt must provide clear context, well-defined action space, and reasoning instructions based on PocketFlow's agent best practices.
## Acceptance Criteria

- [ ] DecideActionNode class created following Node lifecycle
- [ ] Complex agent prompt with CONTEXT and ACTION SPACE sections
- [ ] Prompt includes research template to track progress
- [ ] Action space defines: web_search read_content synthesize finish
- [ ] Each action has clear description and parameters
- [ ] Reasoning process required before action selection
- [ ] Output format as YAML with thinking and action fields
- [ ] Node updates research state based on previous actions

## Implementation Plan

1. Create DecideActionNode class with Node interface\n2. Design comprehensive agent prompt structure\n3. Include CONTEXT section with research goals and current state\n4. Define ACTION SPACE with all available tools\n5. Add reasoning requirement in NEXT ACTION section\n6. Implement prep() to load current research state\n7. Implement exec() with LLM call for decision\n8. Parse action decision and return appropriate action string
