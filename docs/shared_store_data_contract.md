# Shared Store Data Contract

## Overview

The shared store is the central data structure that enables communication between all flows in the Career Application Agent system. This document defines the complete data contract, including all keys, data types, producers, and consumers.

## Data Contract Table

| Key | Data Type | Produced By | Consumed By |
|-----|-----------|-------------|-------------|
| **career_db** | `dict` | Initial Setup / ExperienceDatabaseFlow | RequirementMappingNode, ExperiencePrioritizationNode, CVGenerationNode, CoverLetterNode |
| **job_spec_text** | `str` | Initial Setup (main.py) | ExtractRequirementsNode |
| **job_description** | `str` | Initial Setup (main.py) | ExtractRequirementsNode (alias for job_spec_text) |
| **job_title** | `str` | Initial Setup (main.py) | SuitabilityScoringNode, NarrativeStrategyNode, CVGenerationNode, CoverLetterNode, export_final_materials |
| **company_name** | `str` | Initial Setup (main.py) | CompanyResearchAgent, SuitabilityScoringNode, NarrativeStrategyNode, CVGenerationNode, CoverLetterNode, export_final_materials |
| **company_url** | `str` or `None` | Initial Setup (main.py) | CompanyResearchAgent |
| **current_date** | `str` | Initial Setup (main.py) | CVGenerationNode, CoverLetterNode |
| **requirements** | `dict` | ExtractRequirementsNode | RequirementMappingNode, SuitabilityScoringNode, NarrativeStrategyNode, CVGenerationNode |
| **requirement_mapping_raw** | `list[dict]` | RequirementMappingNode | StrengthAssessmentNode |
| **requirement_mapping_assessed** | `list[dict]` | StrengthAssessmentNode | GapAnalysisNode |
| **requirement_mapping_final** | `list[dict]` | GapAnalysisNode | SuitabilityScoringNode, ExperiencePrioritizationNode |
| **gaps** | `list[dict]` | GapAnalysisNode | SuitabilityScoringNode, NarrativeStrategyNode |
| **coverage_score** | `float` | GapAnalysisNode | SuitabilityScoringNode |
| **company_research** | `dict` | CompanyResearchAgent | SuitabilityScoringNode, NarrativeStrategyNode, CoverLetterNode |
| **suitability_assessment** | `dict` | SuitabilityScoringNode | NarrativeStrategyNode, CVGenerationNode, CoverLetterNode |
| **prioritized_experiences** | `list[dict]` | ExperiencePrioritizationNode | NarrativeStrategyNode |
| **narrative_strategy** | `dict` | NarrativeStrategyNode | CVGenerationNode, CoverLetterNode |
| **cv_markdown** | `str` | CVGenerationNode | export_final_materials |
| **cover_letter_text** | `str` | CoverLetterNode | export_final_materials |
| **checkpoint_data** | `dict` | SaveCheckpointNode | LoadCheckpointNode |
| **enable_company_research** | `bool` | Initial Setup (main.py) | main.py orchestration logic |
| **max_research_iterations** | `int` | Initial Setup (main.py) | CompanyResearchAgent |
| **enable_checkpoints** | `bool` | Initial Setup (main.py) | SaveCheckpointNode |

## Data Type Definitions

### career_db
```python
{
    "personal_info": {
        "name": str,
        "email": str,
        "phone": str,
        "location": str,
        "linkedin": str (optional),
        "github": str (optional),
        "website": str (optional)
    },
    "experience": [
        {
            "title": str,
            "company": str,
            "duration": str,
            "location": str,
            "description": str,
            "achievements": [str],
            "technologies": [str]
        }
    ],
    "education": [
        {
            "degree": str,
            "field": str,
            "institution": str,
            "graduation_year": str,
            "gpa": float (optional),
            "honors": [str] (optional)
        }
    ],
    "skills": {
        "languages": [str],
        "frameworks": [str],
        "databases": [str],
        "cloud": [str],
        "tools": [str]
    },
    "certifications": [str] (optional),
    "publications": [str] (optional),
    "projects": [dict] (optional)
}
```

### requirements
```python
{
    "required": [str],  # List of required qualifications
    "nice_to_have": [str],  # List of preferred qualifications
    "responsibilities": [str] (optional),  # Job responsibilities
    "about_role": str (optional),  # Role description
    "about_company": str (optional)  # Company description
}
```

### requirement_mapping_raw / assessed / final
```python
[
    {
        "requirement": str,  # The requirement text
        "evidence": [str],  # Evidence from career database
        "strength": str,  # "HIGH", "MEDIUM", "LOW" (added in assessed)
        "improvements": [str] (optional)  # Added in final
    }
]
```

### gaps
```python
[
    {
        "requirement": str,  # The missing/weak requirement
        "severity": str,  # "CRITICAL", "IMPORTANT", "NICE_TO_HAVE"
        "mitigation_strategies": [str],  # Ways to address the gap
        "talking_points": [str]  # How to discuss in interview
    }
]
```

### company_research
```python
{
    "mission": str,
    "values": [str],
    "culture": str,
    "team_scope": str,
    "strategic_importance": str,
    "recent_developments": [str],
    "technology_stack_practices": str,
    "market_position_growth": str
}
```

### suitability_assessment
```python
{
    "technical_fit_score": int,  # 0-100
    "cultural_fit_score": int,  # 0-100
    "key_strengths": [str],
    "critical_gaps": [str],
    "unique_value_proposition": str,
    "enthusiasm_authenticity": str,
    "overall_recommendation": str
}
```

### prioritized_experiences
```python
[
    {
        "experience": str,  # Reference to career_db experience
        "relevance_score": int,  # 0-100
        "key_achievements": [str],
        "technologies_used": [str],
        "alignment_points": [str]
    }
]
```

### narrative_strategy
```python
{
    "positioning_statement": str,
    "career_arc": {
        "past": str,
        "present": str,
        "future": str
    },
    "must_tell_experiences": [
        {
            "experience": str,
            "why_relevant": str,
            "key_points": [str]
        }
    ],
    "key_messages": [str],
    "differentiators": [str],
    "evidence_stories": [
        {
            "situation": str,
            "action": str,
            "result": str,
            "relevance": str
        }
    ]
}
```

## Flow Dependencies

### Producer → Consumer Relationships

1. **Initial Setup** (main.py)
   - Produces: career_db, job_spec_text, job_title, company_name, company_url, current_date
   - Consumed by: All flows

2. **RequirementExtractionFlow**
   - Produces: requirements
   - Consumed by: AnalysisFlow, AssessmentFlow, NarrativeFlow, GenerationFlow

3. **AnalysisFlow** (contains 3 nodes)
   - RequirementMappingNode produces: requirement_mapping_raw
   - StrengthAssessmentNode produces: requirement_mapping_assessed
   - GapAnalysisNode produces: requirement_mapping_final, gaps, coverage_score
   - Consumed by: AssessmentFlow, NarrativeFlow

4. **CompanyResearchAgent**
   - Produces: company_research
   - Consumed by: AssessmentFlow, NarrativeFlow, GenerationFlow

5. **AssessmentFlow**
   - Produces: suitability_assessment
   - Consumed by: NarrativeFlow, GenerationFlow

6. **NarrativeFlow** (contains 2 nodes)
   - ExperiencePrioritizationNode produces: prioritized_experiences
   - NarrativeStrategyNode produces: narrative_strategy
   - Consumed by: GenerationFlow

7. **GenerationFlow** (contains 2 nodes)
   - CVGenerationNode produces: cv_markdown
   - CoverLetterNode produces: cover_letter_text
   - Consumed by: export_final_materials

## Validation Rules

1. **Required Keys**: The following keys must be present before their consumer flows:
   - `career_db` must exist before RequirementMappingNode
   - `requirements` must exist before AnalysisFlow
   - `requirement_mapping_final` must exist before AssessmentFlow
   - `narrative_strategy` must exist before GenerationFlow

2. **Type Consistency**: 
   - All scores must be numeric (int or float)
   - All lists must contain items of consistent type
   - Dates must be in YYYY-MM-DD format

3. **Value Constraints**:
   - Scores must be between 0-100
   - Strength values must be one of: "HIGH", "MEDIUM", "LOW"
   - Severity values must be one of: "CRITICAL", "IMPORTANT", "NICE_TO_HAVE"

4. **Checkpoint Keys**: When saving checkpoints, only specified keys should be persisted

## Usage Example

```python
# Initialize shared store
shared = initialize_shared_store(
    career_db=parsed_career_db,
    job_description=job_text,
    job_title="Senior Engineer",
    company_name="TechCorp",
    company_url="https://techcorp.com"
)

# After ExtractRequirementsNode
assert "requirements" in shared
assert isinstance(shared["requirements"], dict)
assert "required" in shared["requirements"]

# After full pipeline
assert shared["cv_markdown"] is not None
assert shared["cover_letter_text"] is not None
```