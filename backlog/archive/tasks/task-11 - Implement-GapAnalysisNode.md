---
id: task-11
title: Implement GapAnalysisNode
status: Done
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-01'
labels: []
dependencies: []
---

## Description

Create a node that identifies gaps in must-have requirements and generates mitigation strategies for each gap. This node compares must-have requirements against assessed mappings, flagging any with LOW strength or no evidence as gaps. For each gap, it uses LLM to brainstorm strategic ways to address the weakness in cover letter or interview. This is critical for honest self-assessment and strategic positioning.

## Acceptance Criteria

- [x] GapAnalysisNode class created following Node lifecycle
- [x] prep reads assessed mapping and original requirements
- [x] Identifies must-have requirements with LOW/no evidence as gaps
- [x] LLM prompt for mitigation strategy generation implemented
- [x] Generates strategic approaches to address each gap
- [x] Mitigation focuses on transferable skills and learning ability
- [x] Final mapping saved to shared['requirement_mapping_final']
- [x] Gaps and strategies saved to shared['gaps']
- [x] Unit tests created for all public methods
- [x] Test coverage of at least 80%
- [x] Mock-based testing for external dependencies (LLM calls, shared store)
- [x] Error cases tested (LLM failures, no gaps found, malformed data)
- [x] Edge cases tested (all requirements are gaps, no must-have requirements)

## Implementation Plan

1. Create GapAnalysisNode class with Node interface
2. Implement prep() to load assessed mappings and requirements
3. Identify gaps: must-haves with LOW strength or missing evidence
4. Design mitigation prompt template
5. For each gap, call LLM to generate mitigation strategy
6. Focus on transferable skills and growth potential
7. Save final mapping to shared store
8. Save gaps list with mitigation strategies

## Completion Summary

**Completed on**: 2025-08-01

### Implementation Details

- Implemented GapAnalysisNode with comprehensive gap identification
- Checks required_skills, experience_years, education, and certifications
- Identifies both missing evidence (no matches) and weak evidence (all LOW scores)
- Generates targeted mitigation strategies using LLM prompts
- Creates final mapping with gap indicators and strength summaries
- Handles errors gracefully with fallback strategies

### Key Features

1. **Gap Detection**: Identifies missing and weak evidence across multiple categories
2. **Strategic Mitigation**: LLM-generated strategies focus on transferable skills and growth
3. **Final Mapping**: Enriches mapping with is_gap flags and strength summaries
4. **Strength Summary**: Hierarchical strength calculation (HIGH > MEDIUM > LOW > NONE)

### Test Coverage

- Created comprehensive test suite with 15 tests
- All tests passing with mocked LLM wrapper
- Covers gap identification, mitigation generation, and error handling
- Tests verify correct handling of various requirement structures

### Notes

- Must-have categories include required_skills, experience_years, education, certifications
- Mitigation prompts emphasize honesty, transferable skills, and learning enthusiasm
- Final mapping provides complete view for downstream narrative generation
