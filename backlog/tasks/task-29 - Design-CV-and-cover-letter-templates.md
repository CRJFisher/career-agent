---
id: task-29
title: Design CV and cover letter templates
status: Complete
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create professional templates and formatting guidelines for the generated CV and cover letter documents. The CV uses GitHub-flavored Markdown for rich formatting including headers, lists, bold/italic text, and links. The cover letter uses plain text with clear paragraph structure. Both templates must be ATS-friendly while maintaining visual appeal. Templates guide the generation nodes to produce consistent, professional output.

## Acceptance Criteria

- [x] CV Markdown template with section headers defined
- [x] Professional summary section at top of CV
- [x] Experience entries with company/role/dates/achievements format
- [x] Skills section with categorized technical skills
- [x] Education and certifications sections included
- [x] Cover letter template with proper business letter format
- [x] 5-part structure clearly delineated in cover letter
- [x] GitHub-flavored Markdown features utilized effectively
- [x] Template validation tests for proper structure and formatting
- [x] Tests verify all required CV sections are included
- [x] Tests validate cover letter 5-part structure implementation
- [x] ATS compatibility tests for both templates
- [x] Markdown syntax validation tests
- [x] Tests ensure templates produce consistent professional output

## Implementation Plan

1. Design CV template structure with main sections
2. Define formatting for experience entries
3. Create skills section with categories
4. Add education/certification formatting
5. Design cover letter header format
6. Structure 5-part cover letter body
7. Ensure ATS compatibility throughout
8. Document formatting guidelines

## Implementation Details

### Files Created

1. **templates/cv_template.md** - Main CV structure with:
   - Professional summary section using blockquotes
   - Core competencies (optional for senior roles)
   - Professional experience with detailed formatting
   - Technical skills with categorization
   - Education and certifications sections
   - ATS optimization guidelines embedded

2. **templates/experience_entry_template.md** - Detailed experience formatting:
   - Role title | Company format
   - Location and date formatting
   - Achievement bullet formula examples
   - Action verb categories
   - Technology list formatting
   - Length guidelines by seniority

3. **templates/skills_section_template.md** - Skills categorization:
   - Programming languages & frameworks
   - Infrastructure & cloud
   - Data & databases
   - Development practices
   - Role-specific templates (Backend, Frontend, Full-Stack, Data Engineer)
   - Proficiency level definitions

4. **templates/education_certification_template.md** - Education/cert formatting:
   - Standard university degree format
   - Multiple degree handling
   - Professional certification format
   - Online courses & specializations
   - Career stage examples

5. **templates/cover_letter_template.txt** - Plain text cover letter:
   - Standard business letter format
   - Multiple header variations
   - Salutation guidelines
   - ATS-friendly formatting rules
   - File format recommendations

6. **templates/cover_letter_5part_structure.md** - 5-part narrative structure:
   - Part 1: The Hook (opening paragraph)
   - Part 2: Relevant Experience & Achievements
   - Part 3: Technical/Domain Expertise
   - Part 4: Cultural Fit & Unique Value
   - Part 5: Call to Action (closing)
   - Examples for each part
   - Length guidelines

7. **templates/ats_compatibility_guide.md** - Comprehensive ATS guide:
   - Universal ATS rules
   - File format preferences
   - Character encoding guidelines
   - Keyword optimization strategies
   - Common parsing errors
   - Testing checklist
   - System-specific quirks

8. **templates/formatting_guidelines.md** - Document formatting standards:
   - GitHub-flavored Markdown features
   - CV style guide
   - Cover letter formatting
   - File export guidelines
   - Quality checklist
   - Accessibility considerations

9. **utils/template_utils.py** - Template utilities:
   - TemplateLoader class for loading templates
   - CVBuilder class for populating CV template
   - CoverLetterBuilder for cover letter generation
   - TemplateValidator for format validation
   - Helper functions for processing

10. **tests/test_template_validation.py** - Comprehensive tests:
    - CVTemplateValidator tests
    - CoverLetterTemplateValidator tests
    - Template integration tests
    - Structure validation
    - ATS compliance checks

11. **templates/README.md** - Template documentation:
    - Overview of all templates
    - Usage instructions
    - Key features summary
    - Testing instructions

### Key Design Decisions

1. **Markdown for CV**: Enables rich formatting while maintaining plain text compatibility
2. **Plain text for cover letter**: Maximum ATS compatibility
3. **5-part structure**: Proven narrative framework for compelling cover letters
4. **Role-specific templates**: Tailored skills sections for different engineering roles
5. **Comprehensive validation**: Ensures all outputs meet formatting requirements
6. **ATS-first design**: Every decision prioritizes ATS parsing success
