---
id: task-4
title: Design career database YAML schema
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Define the structure for the personal career database YAML files that will store professional experiences, projects, skills, and other career-related information. This database represents the ground truth of the applicant's professional history and will be loaded into the Shared Store at startup. The schema must support comprehensive career information including quantified achievements, technologies used, and temporal data.
## Acceptance Criteria

- [ ] YAML schema documented with all required fields
- [ ] Example career database file created
- [ ] Schema includes professional_experience section with roles/achievements
- [ ] Schema includes projects section with descriptions/impact
- [ ] Schema includes skills section (technical/soft skills)
- [ ] Schema includes education and certifications
- [ ] Supports quantified metrics and dates
- [ ] Schema validation rules defined

## Implementation Plan

1. Design top-level structure for career database\n2. Define professional_experience schema with company, role, dates, achievements\n3. Define projects schema with name, description, technologies, impact\n4. Define skills schema categorizing technical and soft skills\n5. Add education and certifications sections\n6. Create comprehensive example file\n7. Document validation rules and required fields
