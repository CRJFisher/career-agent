---
id: task-17
title: Implement CompanyResearchAgent flow
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create the looping agent flow that orchestrates company research using DecideActionNode and tool nodes until research is complete. This implements the canonical agentic loop from PocketFlow documentation where a central decision node directs traffic to tool nodes and loops back for re-evaluation. The agent iterates until DecideActionNode returns 'finish' action, gradually populating the company_research template with mission, team_scope, strategic_importance, and culture information.
## Acceptance Criteria

- [ ] CompanyResearchAgent flow created inheriting from Flow
- [ ] Looping structure with DecideActionNode at center
- [ ] All tool nodes connected with bidirectional edges to DecideNode
- [ ] Action-based routing: search->WebSearchNode read->ReadContentNode etc
- [ ] Research template populated incrementally in shared['company_research']
- [ ] Agent continues until all template fields filled
- [ ] Finish action breaks loop and completes flow
- [ ] Maximum iteration limit to prevent infinite loops
- [ ] Unit tests for flow initialization and graph construction
- [ ] Integration tests for complete research agent execution
- [ ] Tests verify correct action routing to appropriate nodes
- [ ] Tests validate iterative template population
- [ ] Tests ensure proper loop termination conditions
- [ ] Tests verify maximum iteration safety limits

## Implementation Plan

1. Create CompanyResearchAgent class in flow.py\n2. Initialize DecideActionNode and all tool nodes\n3. Define cyclic flow graph with DecideNode as hub\n4. Map actions: 'search'->WebSearchNode, 'read'->ReadContentNode\n5. Map 'synthesize'->SynthesizeInfoNode, 'finish'->end\n6. All tool nodes return to DecideActionNode\n7. Implement iteration counter for safety\n8. Return completed research in shared store
