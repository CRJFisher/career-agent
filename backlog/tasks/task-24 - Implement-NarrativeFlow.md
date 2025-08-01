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

**UPDATED**: Now includes checkpoint functionality for user review.

Create a workflow that chains ExperiencePrioritizationNode and NarrativeStrategyNode to generate the complete narrative strategy, followed by SaveCheckpointNode for user review. This enhanced workflow allows users to review and edit the narrative strategy before document generation. The flow pauses after saving the narrative to an editable YAML file, enabling fine-tuning of the story arc and key themes.

## Acceptance Criteria

- [ ] NarrativeFlow class created in flow.py inheriting from Flow
- [ ] Three nodes connected: Prioritization -> Strategy -> SaveCheckpoint
- [ ] SaveCheckpointNode saves narrative_output.yaml for user review
- [ ] Output file includes editable narrative elements and themes
- [ ] Flow pauses after saving checkpoint
- [ ] LoadCheckpointNode available for resuming workflow
- [ ] Prioritized experiences passed between nodes via shared store
- [ ] Complete narrative strategy preserved in checkpoint
- [ ] User can edit story arc, themes, and experience selection
- [ ] Error handling for all nodes implemented
- [ ] Unit tests for flow initialization and node connection
- [ ] Tests for checkpoint save/load functionality
- [ ] Tests for user edit merging and validation
- [ ] Integration tests for complete narrative flow execution

## Implementation Plan

1. Create NarrativeFlow class inheriting from Flow
2. Initialize three nodes including SaveCheckpointNode
3. Define sequential flow graph with checkpoint
4. Configure SaveCheckpointNode to export narrative elements
5. Connect nodes with proper action mappings
6. Implement pause mechanism after checkpoint save
7. Add support for LoadCheckpointNode on resume
8. Create user-friendly output format
9. Return final narrative strategy after user review

## Dependencies
- SaveCheckpointNode (task-42)
- LoadCheckpointNode (task-43)
