---
id: task-16
title: Implement tool nodes for research agent
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create WebSearchNode, ReadContentNode, and SynthesizeInfoNode that execute the tools selected by DecideActionNode. These nodes are simple wrappers around utility functions but follow PocketFlow Node lifecycle. They receive parameters from DecideActionNode, execute the appropriate utility, and update shared store with results. This separation maintains clean architecture between decision logic and tool execution.
## Acceptance Criteria

- [ ] WebSearchNode class calls utils/web_search.py with query parameter
- [ ] ReadContentNode class calls utils/web_scraper.py with URL parameter
- [ ] SynthesizeInfoNode uses LLM to extract specific info from text
- [ ] All nodes follow prep/exec/post lifecycle pattern
- [ ] Nodes read action parameters from shared store
- [ ] Search results saved to shared['search_results']
- [ ] Scraped content saved to shared['current_content']
- [ ] Synthesized info updates shared['company_research']

## Implementation Plan

1. Create WebSearchNode class using web_search utility\n2. Create ReadContentNode class using web_scraper utility\n3. Create SynthesizeInfoNode with LLM prompt for extraction\n4. Implement prep() to read action parameters\n5. Implement exec() to call respective utilities\n6. Implement post() to save results to shared store\n7. Each node returns to DecideActionNode for next decision\n8. Add error handling for utility failures
