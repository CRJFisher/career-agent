---
id: task-15
title: Implement DecideActionNode
status: Done
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-01'
labels: []
dependencies: []
---

## Description

Create the cognitive core node for the company research agent that decides which tool to use next based on current research state. This implements the Agent pattern's decision-making capability. The node assesses research progress, determines what information is still needed, and selects appropriate tools (web_search, read_content, synthesize, or finish). The prompt must provide clear context, well-defined action space, and reasoning instructions based on PocketFlow's agent best practices.

## Acceptance Criteria

- [x] DecideActionNode class created following Node lifecycle
- [x] Complex agent prompt with CONTEXT and ACTION SPACE sections
- [x] Prompt includes research template to track progress
- [x] Action space defines: web_search read_content synthesize finish
- [x] Each action has clear description and parameters
- [x] Reasoning process required before action selection
- [x] Output format as YAML with thinking and action fields
- [x] Node updates research state based on previous actions
- [x] Unit tests created for all public methods
- [x] Test coverage of at least 80%
- [x] Mock-based testing for external dependencies (LLM calls, shared store)
- [x] Error cases tested (LLM failures, invalid YAML responses, unknown actions)
- [x] Edge cases tested (empty research state, malformed context, action loops)

## Implementation Plan

1. Create DecideActionNode class with Node interface
2. Design comprehensive agent prompt structure
3. Include CONTEXT section with research goals and current state
4. Define ACTION SPACE with all available tools
5. Add reasoning requirement in NEXT ACTION section
6. Implement prep() to load current research state
7. Implement exec() with LLM call for decision
8. Parse action decision and return appropriate action string
