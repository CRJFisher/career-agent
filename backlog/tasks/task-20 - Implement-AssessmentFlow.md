---
id: task-20
title: Implement AssessmentFlow
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a workflow containing the SuitabilityScoringNode that generates the complete suitability assessment. This is a simple single-node flow but crucial for the overall pipeline. The AssessmentFlow takes the outputs from AnalysisFlow (requirement mappings and gaps) and CompanyResearchAgent (company insights) to produce a quantitative and qualitative assessment that guides narrative strategy and material generation.

## Acceptance Criteria

- [ ] AssessmentFlow class created in flow.py inheriting from Flow
- [ ] Single SuitabilityScoringNode instantiated in flow
- [ ] Flow graph: start -> SuitabilityScoringNode -> end
- [ ] Inputs from requirement_mapping_final and gaps processed
- [ ] Company research data incorporated for cultural fit
- [ ] Suitability assessment saved to shared['suitability_assessment']
- [ ] Error handling for scoring failures implemented
- [ ] Assessment data structure properly validated
- [ ] Unit tests for flow initialization and node setup
- [ ] Integration tests for complete assessment flow execution
- [ ] Tests verify proper input data processing from previous flows
- [ ] Tests validate assessment output structure and content
- [ ] Error handling tests for missing or invalid inputs
- [ ] Tests ensure proper shared store state management

## Implementation Plan

1. Create AssessmentFlow class in flow.py
2. Initialize with SuitabilityScoringNode instance
3. Define simple linear flow graph
4. Ensure all required inputs are available
5. Implement run() method for execution
6. Validate assessment output structure
7. Handle edge cases and errors
8. Return completed assessment state
