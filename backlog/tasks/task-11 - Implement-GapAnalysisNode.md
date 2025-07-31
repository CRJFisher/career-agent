---
id: task-11
title: Implement GapAnalysisNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a node that identifies gaps in must-have requirements and generates mitigation strategies for each gap. This node compares must-have requirements against assessed mappings, flagging any with LOW strength or no evidence as gaps. For each gap, it uses LLM to brainstorm strategic ways to address the weakness in cover letter or interview. This is critical for honest self-assessment and strategic positioning.

## Acceptance Criteria

- [ ] GapAnalysisNode class created following Node lifecycle
- [ ] prep reads assessed mapping and original requirements
- [ ] Identifies must-have requirements with LOW/no evidence as gaps
- [ ] LLM prompt for mitigation strategy generation implemented
- [ ] Generates strategic approaches to address each gap
- [ ] Mitigation focuses on transferable skills and learning ability
- [ ] Final mapping saved to shared['requirement_mapping_final']
- [ ] Gaps and strategies saved to shared['gaps']
- [ ] Unit tests created for all public methods
- [ ] Test coverage of at least 80%
- [ ] Mock-based testing for external dependencies (LLM calls, shared store)
- [ ] Error cases tested (LLM failures, no gaps found, malformed data)
- [ ] Edge cases tested (all requirements are gaps, no must-have requirements)

## Implementation Plan

1. Create GapAnalysisNode class with Node interface\n2. Implement prep() to load assessed mappings and requirements\n3. Identify gaps: must-haves with LOW strength or missing evidence\n4. Design mitigation prompt template\n5. For each gap, call LLM to generate mitigation strategy\n6. Focus on transferable skills and growth potential\n7. Save final mapping to shared store\n8. Save gaps list with mitigation strategies
