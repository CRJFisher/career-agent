---
id: task-24
title: Implement NarrativeFlow
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a workflow that chains ExperiencePrioritizationNode and NarrativeStrategyNode to generate the complete narrative strategy. This workflow first uses algorithmic scoring to rank all experiences objectively, then applies strategic thinking via LLM to select and craft the narrative. The two-step process ensures both data-driven prioritization and creative storytelling for maximum impact.
## Acceptance Criteria

- [ ] NarrativeFlow class created in flow.py inheriting from Flow
- [ ] ExperiencePrioritizationNode and NarrativeStrategyNode connected
- [ ] Flow graph: start -> ExperiencePrioritization -> NarrativeStrategy -> end
- [ ] Prioritized experiences passed between nodes via shared store
- [ ] Suitability assessment available to strategy node
- [ ] Complete narrative strategy saved to shared['narrative_strategy']
- [ ] Both algorithmic and creative aspects balanced
- [ ] Error handling for both nodes implemented

## Implementation Plan

1. Create NarrativeFlow class inheriting from Flow\n2. Initialize both nodes in constructor\n3. Define sequential flow graph\n4. Connect nodes with proper action mappings\n5. Ensure prioritized list passes to strategy node\n6. Make assessment data available for context\n7. Implement run() method for execution\n8. Return final narrative strategy
