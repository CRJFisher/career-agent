---
id: task-4
title: Design career database YAML schema
status: Done
assignee:
  - '@claude'
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Define the structure for the personal career database YAML files that will store professional experiences, projects, skills, and other career-related information. This database represents the ground truth of the applicant's professional history and will be loaded into the Shared Store at startup. The schema must support comprehensive career information including quantified achievements, technologies used, and temporal data.

## Acceptance Criteria

- [x] YAML schema documented with all required fields
- [x] Example career database file created
- [x] Schema includes professional_experience section with roles/achievements
- [x] Schema includes projects section with descriptions/impact
- [x] Schema includes skills section (technical/soft skills)
- [x] Schema includes education and certifications
- [x] Supports quantified metrics and dates
- [x] Schema validation rules defined

## Implementation Plan

1. Design top-level structure for career database
2. Define professional_experience schema with company, role, dates, achievements
3. Define projects schema with name, description, technologies, impact
4. Define skills schema categorizing technical and soft skills
5. Add education and certifications sections
6. Create comprehensive example file
7. Document validation rules and required fields

## Implementation Notes

- Created comprehensive career_database_schema.md documentation in docs/
- Defined clear schema with required and optional fields for all sections
- Example file already existed from task-3, contains all schema elements
- Created JSON Schema file for programmatic validation
- Added validate_with_schema() function to database_parser.py
- Schema supports:
  - Personal info with contact details and online profiles
  - Experience entries with quantified achievements and technologies
  - Education with GPA, honors, and coursework
  - Categorized skills (technical, soft, languages, tools, frameworks)
  - Projects with outcomes and technologies
  - Certifications with expiry and verification
  - Publications and awards sections
- Validation rules include:
  - Required sections: personal_info, experience, education, skills
  - Date format validation with regex patterns
  - Minimum items for required lists
  - Email and URI format validation
- Added jsonschema dependency for validation
- Best practices documented for quantifying impact and consistent naming
