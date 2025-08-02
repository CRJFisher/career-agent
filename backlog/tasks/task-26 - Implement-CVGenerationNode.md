---
id: task-26
title: Implement CVGenerationNode
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create a node that generates a tailored CV in GitHub-flavored Markdown format based on narrative strategy and career database. The node acts as a professional resume writer, emphasizing experiences identified in the narrative strategy while drawing quantified details from the career database. The CV must mirror job specification language and highlight achievements with metrics. Output is formatted Markdown ready for conversion to PDF or other formats.

## Acceptance Criteria

- [x] CVGenerationNode class created following Node lifecycle
- [x] Professional resume writer prompt implemented
- [x] Reads narrative_strategy for experience prioritization
- [x] Draws detailed data from career_db for accuracy
- [x] Emphasizes must-tell experiences prominently
- [x] Minimizes or summarizes lower-priority experiences
- [x] Mirrors job specification language throughout
- [x] GitHub-flavored Markdown with proper formatting
- [x] Unit tests for CV generation node lifecycle methods
- [x] Tests verify proper integration of narrative strategy data
- [x] Tests validate career database information extraction
- [x] Tests ensure must-tell experiences are prominently featured
- [x] Tests verify proper Markdown formatting and structure
- [x] Tests validate job specification language mirroring
- [x] Output validation tests for generated CV completeness

## Implementation Plan

1. Create CVGenerationNode class with Node interface
2. Design professional resume writer prompt
3. Include narrative strategy as primary guide
4. Reference career_db for complete information
5. Emphasize experiences from must_tell list
6. Add quantified achievements and metrics
7. Use job spec language for keyword matching
8. Output clean Markdown to shared['cv_markdown']

## Implementation Notes & Findings

### Node Architecture

Successfully implemented CVGenerationNode as an LLM-driven node that:
- Takes narrative strategy as the primary guide for CV structure
- Draws detailed data from career database for accuracy
- Uses job requirements for keyword optimization
- Outputs GitHub-flavored Markdown format

### Prompt Design

The CV generation prompt includes:
1. **Role**: Expert resume writer specializing in technical roles
2. **Context**: Target job title and company name
3. **Narrative Strategy**: All 5 components (must-tells, differentiators, arc, messages, stories)
4. **Requirements**: Formatted list of required/preferred skills and experience
5. **Career Database**: Full details with must-tell experiences marked
6. **Instructions**: 7 specific guidelines for CV creation
7. **Output Format**: Complete markdown template with sections

### Key Features

1. **Must-Tell Prioritization**:
   - Prompt explicitly marks must-tell experiences with `[MUST-TELL]`
   - These get expanded bullet points
   - Other experiences are summarized briefly

2. **Job Spec Mirroring**:
   - Extracts all skills from requirements (required, preferred, technologies)
   - Instructs LLM to use job specification language throughout
   - Ensures keyword optimization for ATS

3. **Narrative Integration**:
   - Professional summary incorporates all 3 key messages
   - Differentiators highlighted in summary
   - Career arc progression reflected in experience ordering

4. **Fallback Strategy**:
   - Robust fallback CV generation if LLM fails
   - Uses career database and narrative strategy directly
   - Ensures user always gets a CV output

### Markdown Format

The generated CV follows GitHub-flavored Markdown with:
- `#` for name (H1)
- `##` for major sections (H2)
- `###` for job titles (H3)
- `-` for bullet points
- `**bold**` for emphasis
- Proper spacing between sections

### Testing Coverage

Created 19 comprehensive tests covering:
- Input validation (narrative strategy, career database)
- Prompt content verification (all elements included)
- Must-tell experience prioritization
- Fallback CV generation
- Markdown formatting validation
- Edge cases (missing data, empty sections)
- Logging and output storage

### Error Handling

1. **LLM Failures**: Falls back to deterministic CV generation
2. **Short Responses**: Triggers fallback if CV < 500 characters
3. **Missing Data**: Handles missing personal info, empty sections gracefully
4. **Empty Inputs**: Validates against empty dictionaries

### Integration Points

The node integrates with:
- **NarrativeStrategyNode**: Reads narrative_strategy for prioritization
- **Career Database**: Reads career_db for detailed experience data
- **Requirements**: Uses requirements for keyword optimization
- **GenerationFlow**: Outputs cv_markdown for document generation

### Prompt Engineering Insights

1. **Explicit Marking**: Using `[MUST-TELL]` ensures LLM prioritizes correctly
2. **Structured Context**: Separating narrative, requirements, and career data improves focus
3. **Clear Instructions**: Numbered guidelines improve compliance
4. **Template Provision**: Showing exact markdown format improves consistency

### Future Enhancements

1. **Multiple Formats**: Support for different CV styles (academic, executive, etc.)
2. **Length Variants**: 1-page vs 2-page versions
3. **ATS Optimization**: Specific keyword density targets
4. **Industry Customization**: Tailor format to industry norms
5. **Visual Elements**: Support for skills visualizations
