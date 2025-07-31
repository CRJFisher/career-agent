---
id: task-10
title: Implement StrengthAssessmentNode
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create a node that evaluates the strength of requirement-to-evidence mappings using LLM to assign HIGH, MEDIUM, or LOW scores. This node performs qualitative synthesis by analyzing how well each piece of evidence demonstrates the required skill. HIGH means direct and powerful demonstration, MEDIUM shows related experience, LOW indicates weak or indirect link. This assessment is crucial for identifying gaps and prioritizing experiences.
## Acceptance Criteria

- [ ] StrengthAssessmentNode class created following Node lifecycle
- [ ] prep reads raw mapping from shared['requirement_mapping_raw']
- [ ] Iterates through each requirement and its evidence list
- [ ] LLM prompt for qualitative strength assessment implemented
- [ ] Assigns HIGH/MEDIUM/LOW scores based on match quality
- [ ] Prompt template includes requirement evidence and scoring criteria
- [ ] Assessed mapping saved to shared['requirement_mapping_assessed']
- [ ] Maintains original evidence with added strength scores

## Implementation Plan

1. Create StrengthAssessmentNode class inheriting from Node\n2. Implement prep() to read raw requirement mappings\n3. Design LLM prompt for strength assessment\n4. Include scoring criteria in prompt (HIGH/MEDIUM/LOW definitions)\n5. Iterate through each requirement-evidence pair\n6. Call LLM to assess match strength\n7. Update mapping structure with strength scores\n8. Save assessed mapping to shared store in post()
