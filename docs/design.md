# PocketFlow Career Application Agent Design

## Overview

This system automates the customization of job applications using The-Pocket/PocketFlow framework - a minimalist 100-line LLM orchestration framework that models applications as directed graphs.

## Core Concepts

### 1. Nodes (Discrete Units of Work)

- **ExtractRequirementsNode**: Parses job descriptions into structured requirements
- **RequirementMappingNode**: Maps candidate experience to job requirements  
- **StrengthAssessmentNode**: Evaluates candidate strengths
- **GapAnalysisNode**: Identifies missing qualifications
- **DecideActionNode**: Determines research needs
- **CompanyResearchNode**: Gathers company information
- **SuitabilityScoringNode**: Calculates fit score
- **ExperiencePrioritizationNode**: Ranks relevant experiences
- **NarrativeStrategyNode**: Develops application narrative
- **CVGenerationNode**: Creates tailored CV
- **CoverLetterNode**: Generates cover letter

### 2. Flows (Directed Graphs)

- **RequirementExtractionFlow**: Job parsing pipeline
- **AnalysisFlow**: Candidate evaluation pipeline  
- **CompanyResearchFlow**: Information gathering pipeline
- **AssessmentFlow**: Suitability scoring pipeline
- **NarrativeFlow**: Story development pipeline
- **GenerationFlow**: Document creation pipeline

### 3. Shared Store (Data Repository)

Central data store containing:

- Career database (candidate information)
- Job requirements
- Analysis results
- Research findings
- Generated documents

## Data Flow

```txt
Job Description → RequirementExtractionFlow → Structured Requirements
                                                        ↓
Career Database → AnalysisFlow → Strengths/Gaps Analysis
                                          ↓
Company URL → CompanyResearchFlow → Company Insights
                                          ↓
                    AssessmentFlow → Suitability Score
                                          ↓
                     NarrativeFlow → Application Strategy
                                          ↓
                    GenerationFlow → CV + Cover Letter
```

## Key Design Decisions

1. **Modular Architecture**: Each node handles one specific task
2. **Async Execution**: Nodes can run in parallel where dependencies allow
3. **YAML-based Data**: Human-readable configuration and outputs
4. **LLM Integration**: Nodes leverage language models for intelligent processing
5. **Extensibility**: Easy to add new nodes or modify flows

## Implementation Notes

- Following PocketFlow's minimalist philosophy
- Core framework files: nodes.py, flow.py, main.py
- Utilities isolated in utils/ directory
- Clear separation between orchestration and business logic
