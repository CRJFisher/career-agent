---
id: task-23
title: Implement NarrativeStrategyNode
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create an LLM-driven node that synthesizes a complete narrative strategy including must-tell experiences, differentiators, career arc, key messages, and evidence stories. This sophisticated node acts as an expert career coach, taking the prioritized experience list and suitability assessment to craft a compelling application narrative. The node selects top experiences, formulates career progression story, and creates detailed CAR (Challenge, Action, Result) format evidence stories.

## Acceptance Criteria

- [x] NarrativeStrategyNode class created following Node lifecycle
- [x] Career storyteller prompt for strategic synthesis
- [x] Selects top 2-3 must-tell experiences from ranked list
- [x] Identifies 1-2 unique differentiator experiences
- [x] Formulates career arc narrative (past present future)
- [x] Defines 3 concise key messages for application
- [x] Creates 1-2 detailed CAR format evidence stories
- [x] Complete narrative_strategy dict saved to shared store
- [x] Unit tests for node initialization and lifecycle methods
- [x] Tests verify experience selection logic (top 2-3 must-tells)
- [x] Tests validate differentiator identification accuracy
- [x] Tests ensure career arc narrative coherence
- [x] Tests verify key message generation quality and count
- [x] Tests validate CAR story format and completeness
- [x] Mock LLM tests for prompt handling and response parsing

## Implementation Plan

1. Create NarrativeStrategyNode class with Node interface
2. Design expert career coach prompt
3. Implement experience selection logic (top 2-3 must-tells)
4. Add differentiator identification (1-2 unique experiences)
5. Include career arc formulation instructions
6. Define key message generation requirements
7. Add CAR story format template and examples
8. Output comprehensive narrative strategy

## Implementation Notes & Findings

### LLM-Driven Strategy Synthesis

Successfully implemented an expert career coach node that:

- Takes prioritized experiences from ExperiencePrioritizationNode
- Incorporates suitability assessment insights
- Generates comprehensive narrative strategy in one LLM call
- Validates and fills missing fields for robustness

### Prompt Design

The prompt adopts an expert career coach perspective with:

1. **Context Section**: Job details, suitability scores, and top 5 prioritized experiences
2. **Task Instructions**: Clear guidance for each narrative component
3. **Output Format**: Structured YAML with examples for each section

Key prompt elements:

- Shows experience scores (composite, relevance, impact) to guide selection
- Emphasizes rare skill combinations for differentiators
- Requires past→present→future career arc structure
- Mandates CAR format for evidence stories

### Narrative Components

1. **Must-Tell Experiences (2-3)**:
   - Selected based on highest impact + relevance
   - Each includes reason for selection and key points
   - Demonstrates required skills and progression

2. **Differentiators (1-2)**:
   - Unique aspects that set candidate apart
   - Focus on rare skill intersections
   - Derived from unique value proposition

3. **Career Arc**:
   - Past: Foundation and early growth
   - Present: Current expertise and leadership
   - Future: Vision for target role (mentions company)

4. **Key Messages (3)**:
   - Core value propositions
   - Proactive concern addressing
   - Company alignment

5. **Evidence Stories (1-2)**:
   - Full CAR format: Challenge, Action, Result
   - Includes skills demonstrated
   - Substantial detail (50+ chars per section)

### Experience Processing

- Formats top 5 experiences with scores for LLM context
- Summarizes experience data including company, achievements, technologies
- Handles various experience types (professional, project, education)

### Error Handling

Robust fallback strategy ensures node always produces valid output:

- Uses top 3 experiences for must-tells
- Extracts differentiators from suitability assessment
- Provides generic but reasonable career arc
- Returns empty evidence stories rather than failing

### Field Validation

Post-LLM validation ensures all required fields are present:

- Missing must-tell experiences → uses top 3 prioritized
- Missing differentiators → extracts from unique value proposition
- Missing career arc → provides template based on job title
- Missing key messages → generates standard value props
- Missing evidence stories → returns empty list

### Testing Coverage

Created 17 comprehensive tests covering:

- Input validation (missing data)
- Prompt content verification
- Experience selection logic
- Differentiator identification
- Career arc structure
- Key message count and quality
- CAR story format validation
- Error handling and fallback
- Field filling for incomplete responses
- Edge cases (empty assessment, many experiences)

### Integration Points

- Requires `prioritized_experiences` from ExperiencePrioritizationNode
- Requires `suitability_assessment` from SuitabilityScoringNode
- Uses `requirements`, `job_title`, and `company_name` from shared store
- Outputs to `narrative_strategy` for document generation
- Returns "narrative" action for flow routing

### Key Design Decisions

1. **Single LLM Call**: All narrative components generated together for coherence
2. **Top 5 Context**: Provides enough options without overwhelming the LLM
3. **Score Visibility**: Shows relevance and impact scores to guide selection
4. **Structured Output**: YAML format ensures consistent parsing
5. **Graceful Degradation**: Always produces usable output even on errors

### Future Enhancements

1. **Multi-stage Refinement**: Could iterate on narrative based on feedback
2. **Industry Customization**: Tailor narrative style to industry norms
3. **Length Variants**: Generate short/medium/long versions
4. **A/B Testing**: Test different narrative strategies for effectiveness
