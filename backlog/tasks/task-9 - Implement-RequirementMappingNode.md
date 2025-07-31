---
id: task-9
title: Implement RequirementMappingNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a node that maps job requirements to personal experiences using RAG pattern to search career database for relevant evidence. This is the first node in the AnalysisFlow and implements a form of Retrieval-Augmented Generation where retrieval (searching the database) provides context to generation (creating the mapping). The node must iterate through each requirement and find all potentially relevant pieces of evidence from professional_experience and projects sections.
## Acceptance Criteria

- [ ] RequirementMappingNode class created in nodes.py following Node lifecycle
- [ ] prep reads requirements from shared['job_requirements_structured'] and career_db
- [ ] RAG search functionality implemented for evidence retrieval
- [ ] Searches both professional_experience and projects sections
- [ ] Supports keyword matching for initial implementation
- [ ] Semantic search capability planned for enhancement
- [ ] Raw mapping saved to shared['requirement_mapping_raw']
- [ ] Each requirement mapped to list of potential evidence

## Implementation Plan

1. Create RequirementMappingNode class with PocketFlow Node interface\n2. Implement prep() to load requirements and career database\n3. Design retrieval logic to search career_db for each requirement\n4. Implement keyword matching across experience descriptions\n5. Search both professional_experience and projects for evidence\n6. Create mapping structure: {requirement: [evidence_list]}\n7. Implement post() to save raw mapping to shared store\n8. Return 'continue' action for flow progression
