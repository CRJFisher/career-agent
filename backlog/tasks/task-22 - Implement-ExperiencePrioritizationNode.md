---
id: task-22
title: Implement ExperiencePrioritizationNode
status: Completed
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create a pure Python node that scores and ranks all career experiences using weighted criteria. This node does NOT require LLM - it implements the user's explicit scoring framework with weights: relevance_to_role (40%), recency (20%), impact (20%), uniqueness (10%), growth (10%). The node iterates through every item in career_db and produces a ranked list that guides narrative prioritization. This algorithmic approach ensures consistent, explainable prioritization.

## Acceptance Criteria

- [x] ExperiencePrioritizationNode class created with pure Python logic
- [x] No LLM calls - implements deterministic scoring algorithm
- [x] Weighted scoring: relevance 40% recency 20% impact 20% uniqueness 10% growth 10%
- [x] Processes all professional_experience entries from career_db
- [x] Processes all projects entries from career_db
- [x] Calculates composite score for each experience
- [x] Returns sorted list by score (highest first)
- [x] Scoring methodology documented in code
- [x] Unit tests for each scoring criterion function
- [x] Tests verify weighted calculation accuracy (40/20/20/10/10)
- [x] Tests validate proper handling of all career_db entries
- [x] Tests ensure correct sorting by composite score
- [x] Edge case tests for missing dates or incomplete experience data
- [x] Tests verify scoring consistency and deterministic results
- [x] Performance tests for large career databases

## Implementation Plan

1. Create ExperiencePrioritizationNode class
2. Implement prep() to load career_db and requirements
3. Define scoring functions for each criterion
4. Implement relevance scoring against job requirements
5. Calculate recency score based on dates
6. Extract impact score from quantified achievements
7. Assess uniqueness and growth demonstration
8. Sort experiences by composite score

## Implementation Notes & Findings

### Pure Python Implementation

Successfully implemented a deterministic scoring algorithm without any LLM calls:
- Used weighted scoring with exact percentages: relevance (40%), recency (20%), impact (20%), uniqueness (10%), growth (10%)
- All scoring functions return values 0-100 for consistency
- Composite score is calculated as weighted sum, ensuring reproducible results

### Scoring Methodology Details

1. **Relevance Scoring (40%)**:
   - Matches experience text against required skills, preferred skills, and technologies
   - Case-insensitive matching for flexibility
   - Industry match gets bonus weight (2x)
   - Score = (matches / total_possible) * 100

2. **Recency Scoring (20%)**:
   - "Present" or missing dates get 100 (assumed current)
   - Decreases by 10 points per year (100 for current, 90 for 1 year ago, etc.)
   - Minimum score of 0 for experiences 10+ years old
   - Handles unparseable dates gracefully with default score of 50

3. **Impact Scoring (20%)**:
   - Searches for impact keywords: increased, decreased, improved, reduced, saved, etc.
   - Quantified achievements (containing numbers) get 2x weight
   - Score = min(100, indicators * 20) - caps at 100 for 5+ indicators

4. **Uniqueness Scoring (10%)**:
   - Calculates Jaccard similarity with other experiences
   - Extracts terms > 4 characters for meaningful comparison
   - Score = (1 - average_similarity) * 100
   - Experiences with no similar terms score 100

5. **Growth Scoring (10%)**:
   - Searches for growth indicators: promoted, led, managed, senior, etc.
   - Team size mentions get 2x weight (regex patterns for "team of X", "X engineers", etc.)
   - Score = min(100, indicators * 20)

### Data Processing

The node processes three types of experiences:
1. **Professional Experience**: All entries from career_db["professional_experience"]
2. **Projects**: All entries from career_db["projects"]
3. **Education**: Only included if has achievements or projects

### Text Extraction

Implemented recursive text extraction that:
- Concatenates all string fields
- Flattens lists of strings
- Recursively extracts from nested dictionaries
- Provides comprehensive text for scoring functions

### Performance Optimization

- No retry logic needed (deterministic algorithm)
- Efficient text processing using Python built-ins
- Tested with 100+ experiences completing in < 1 second
- Memory efficient with streaming processing

### Output Format

The prioritized_experiences list contains:
```python
{
    "rank": 1,  # 1-based ranking
    "title": "Senior Software Engineer",
    "type": "professional",  # or "project", "education"
    "composite_score": 78.5,  # Weighted score
    "scores": {
        "relevance": 85.0,
        "recency": 100.0,
        "impact": 60.0,
        "uniqueness": 45.0,
        "growth": 70.0
    },
    "data": {...}  # Original experience data
}
```

### Testing Coverage

Created 18 comprehensive tests covering:
- Weight validation (sum to 1.0)
- Individual scoring functions
- Composite score calculation
- Deterministic results (multiple runs produce identical output)
- Edge cases (empty DB, missing dates, no requirements)
- Performance with large databases (10, 50, 100 experiences)
- Text extraction from complex nested structures

### Key Insights

1. **Deterministic Design**: Pure Python implementation ensures consistent results across runs
2. **Balanced Scoring**: 40% relevance weight ensures job-fit is primary factor while other criteria add nuance
3. **Graceful Degradation**: Missing data gets sensible defaults rather than causing errors
4. **Explainability**: Each score component is transparent and can be traced

### Integration Points

- Expects `career_db` with standard schema from database parser
- Uses `requirements` from ExtractRequirementsNode
- Outputs to `prioritized_experiences` for use by narrative generation
- Action returns "prioritize" for flow routing
