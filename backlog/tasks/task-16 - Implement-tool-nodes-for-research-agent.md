---
id: task-16
title: Implement tool nodes for research agent
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create WebSearchNode, ReadContentNode, and SynthesizeInfoNode that execute the tools selected by DecideActionNode. These nodes are simple wrappers around utility functions but follow PocketFlow Node lifecycle. They receive parameters from DecideActionNode, execute the appropriate utility, and update shared store with results. This separation maintains clean architecture between decision logic and tool execution.

## Acceptance Criteria

- [x] WebSearchNode class calls utils/web_search.py with query parameter
- [x] ReadContentNode class calls utils/web_scraper.py with URL parameter
- [x] SynthesizeInfoNode uses LLM to extract specific info from text
- [x] All nodes follow prep/exec/post lifecycle pattern
- [x] Nodes read action parameters from shared store
- [x] Search results saved to shared['search_results']
- [x] Scraped content saved to shared['current_content']
- [x] Synthesized info updates shared['company_research']
- [x] Unit tests written for all three node classes
- [x] Tests verify proper utility function calls with correct parameters
- [x] Tests validate shared store updates with expected data structures
- [x] Error handling tests for utility failures
- [x] Mock-based tests to isolate node behavior from external dependencies

## Implementation Plan

1. Create WebSearchNode class using web_search utility
2. Create ReadContentNode class using web_scraper utility
3. Create SynthesizeInfoNode with LLM prompt for extraction
4. Implement prep() to read action parameters
5. Implement exec() to call respective utilities
6. Implement post() to save results to shared store
7. Each node returns to DecideActionNode for next decision
8. Add error handling for utility failures
