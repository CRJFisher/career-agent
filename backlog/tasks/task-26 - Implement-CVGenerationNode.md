---
id: task-26
title: Implement CVGenerationNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a node that generates a tailored CV in GitHub-flavored Markdown format based on narrative strategy and career database. The node acts as a professional resume writer, emphasizing experiences identified in the narrative strategy while drawing quantified details from the career database. The CV must mirror job specification language and highlight achievements with metrics. Output is formatted Markdown ready for conversion to PDF or other formats.
## Acceptance Criteria

- [ ] CVGenerationNode class created following Node lifecycle
- [ ] Professional resume writer prompt implemented
- [ ] Reads narrative_strategy for experience prioritization
- [ ] Draws detailed data from career_db for accuracy
- [ ] Emphasizes must-tell experiences prominently
- [ ] Minimizes or summarizes lower-priority experiences
- [ ] Mirrors job specification language throughout
- [ ] GitHub-flavored Markdown with proper formatting

## Implementation Plan

1. Create CVGenerationNode class with Node interface\n2. Design professional resume writer prompt\n3. Include narrative strategy as primary guide\n4. Reference career_db for complete information\n5. Emphasize experiences from must_tell list\n6. Add quantified achievements and metrics\n7. Use job spec language for keyword matching\n8. Output clean Markdown to shared['cv_markdown']
