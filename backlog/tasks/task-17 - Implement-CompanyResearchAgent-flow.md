---
id: task-17
title: Implement CompanyResearchAgent flow
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create the looping agent flow that orchestrates company research using DecideActionNode and tool nodes until research is complete. This implements the canonical agentic loop from PocketFlow documentation where a central decision node directs traffic to tool nodes and loops back for re-evaluation. The agent iterates until DecideActionNode returns 'finish' action, gradually populating the company_research template with mission, team_scope, strategic_importance, and culture information.

## Acceptance Criteria

- [x] CompanyResearchAgent flow created inheriting from Flow
- [x] Looping structure with DecideActionNode at center
- [x] All tool nodes connected with bidirectional edges to DecideNode
- [x] Action-based routing: search->WebSearchNode read->ReadContentNode etc
- [x] Research template populated incrementally in shared['company_research']
- [x] Agent continues until all template fields filled
- [x] Finish action breaks loop and completes flow
- [x] Maximum iteration limit to prevent infinite loops
- [x] Unit tests for flow initialization and graph construction
- [x] Integration tests for complete research agent execution
- [x] Tests verify correct action routing to appropriate nodes
- [x] Tests validate iterative template population
- [x] Tests ensure proper loop termination conditions
- [x] Tests verify maximum iteration safety limits

## Implementation Plan

1. Create CompanyResearchAgent class in flow.py
2. Initialize DecideActionNode and all tool nodes
3. Define cyclic flow graph with DecideNode as hub
4. Map actions: 'search'->WebSearchNode, 'read'->ReadContentNode
5. Map 'synthesize'->SynthesizeInfoNode, 'finish'->end
6. All tool nodes return to DecideActionNode
7. Implement iteration counter for safety
8. Return completed research in shared store
