# Career Application Agent - System Workflow

## Overview

This document visualizes the complete workflow of the Career Application Agent system, showing how different flows and nodes interact to process job applications.

## High-Level System Architecture

```mermaid
flowchart TB
    subgraph Data Sources
        GD[Google Drive Docs]
        LF[Local Files]
        JD[Job Description]
    end
    
    subgraph Main Flows
        EDF[ExperienceDatabaseFlow]
        REF[RequirementExtractionFlow]
        AF[AnalysisFlow]
        CRF[CompanyResearchFlow]
        ASF[AssessmentFlow]
        NF[NarrativeFlow]
        GF[GenerationFlow]
    end
    
    subgraph User Review Points
        UR1[User Review 1]
        UR2[User Review 2]
    end
    
    subgraph Output
        CD[Career Database]
        CV[CV/Resume]
        CL[Cover Letter]
        AR[Analysis Report]
    end
    
    GD --> EDF
    LF --> EDF
    EDF --> CD
    JD --> REF
    CD --> AF
    REF --> AF
    AF --> UR1
    UR1 --> CRF
    CRF --> ASF
    UR1 --> ASF
    ASF --> NF
    NF --> UR2
    UR2 --> GF
    GF --> CV
    GF --> CL
    ASF --> AR
```

## Detailed Flow Breakdown

### 1. Experience Database Flow (New)

```mermaid
flowchart LR
    Start([Document Sources]) --> SDN[ScanDocumentsNode]
    SDN --> EEN[ExtractExperienceNode]
    EEN --> BDN[BuildDatabaseNode]
    BDN --> End([Career Database])
    
    subgraph ScanDocumentsNode
        GDS[Google Drive Scan] --> List[Document List]
        LFS[Local Folder Scan] --> List
    end
    
    subgraph ExtractExperienceNode
        PDF[PDF Parser] --> Extract[Extract Work Info]
        MD[Markdown Parser] --> Extract
        DOC[Doc Parser] --> Extract
    end
    
    subgraph BuildDatabaseNode
        Structure[Structure Data] --> Validate[Validate Schema]
    end
```

### 2. Requirement Extraction Flow

```mermaid
flowchart LR
    Start([Job Description]) --> ERN[ExtractRequirementsNode]
    ERN --> |"YAML output"| End([Requirements YAML])
    
    subgraph ExtractRequirementsNode
        Parse[Parse JD] --> Extract[Extract Key Info]
        Extract --> Structure[Structure as YAML]
    end
```

### 3. Analysis Flow (With User Review)

```mermaid
flowchart LR
    Start([Requirements + Career DB]) --> RMN[RequirementMappingNode]
    RMN --> SAN[StrengthAssessmentNode]
    SAN --> GAN[GapAnalysisNode]
    GAN --> SCN[SaveCheckpointNode]
    SCN --> End([Analysis Output])
    
    subgraph RequirementMappingNode
        Map[Map Requirements<br/>to Experience]
    end
    
    subgraph StrengthAssessmentNode
        Assess[Assess Match<br/>Strength]
    end
    
    subgraph GapAnalysisNode
        Identify[Identify Gaps &<br/>Opportunities]
    end
    
    subgraph SaveCheckpointNode
        Save[Save to YAML] --> Notify[Notify User<br/>for Review]
    end
```

**User Review Point**: After analysis completes, the system saves `analysis_output.yaml` and pauses for user review/editing.

### 4. Company Research Flow (AI-Browser Agent)

```mermaid
flowchart TD
    Start([Company Name]) --> LCN[LoadCheckpointNode]
    LCN --> DAN[DecideActionNode]
    DAN -->|search| BAN[BrowserActionNode]
    DAN -->|navigate| SN[SearchNode]
    DAN -->|extract| EIN[ExtractInfoNode]
    DAN -->|analyze| CAN[CompanyAnalysisNode]
    DAN -->|complete| End([Company Research])
    
    BAN --> DAN
    SN --> DAN
    EIN --> DAN
    CAN --> DAN
    
    subgraph AI Browser Agent
        BAN -->|Google Search| SN
        SN -->|Click Links| BAN
        BAN -->|Extract Content| EIN
    end
```

**Key Features**:
- Uses AI-driven headless browser for complex interactions
- Can handle dynamic content and JavaScript-heavy sites
- Navigates Google search results intelligently
- Resumes from checkpoint after user review

### 4. Assessment Flow

```mermaid
flowchart LR
    Start([Analysis + Research]) --> SSN[SuitabilityScoringNode]
    SSN --> End([Suitability Score])
    
    subgraph SuitabilityScoringNode
        Culture[Culture Fit] --> Score[Calculate Score]
        Tech[Tech Match] --> Score
        Growth[Growth Potential] --> Score
    end
```

### 6. Narrative Flow (With User Review)

```mermaid
flowchart LR
    Start([Assessment Results]) --> EPN[ExperiencePrioritizationNode]
    EPN --> NSN[NarrativeStrategyNode]
    NSN --> SCN[SaveCheckpointNode]
    SCN --> End([Narrative Output])
    
    subgraph ExperiencePrioritizationNode
        Rank[Rank Experiences<br/>by Relevance]
    end
    
    subgraph NarrativeStrategyNode
        Theme[Define Themes] --> Story[Create Story Arc]
    end
    
    subgraph SaveCheckpointNode
        Save[Save to YAML] --> Notify[Notify User<br/>for Review]
    end
```

**User Review Point**: After narrative strategy completes, the system saves `narrative_output.yaml` and pauses for user review/editing.

### 7. Generation Flow

```mermaid
flowchart LR
    Start([User-Reviewed Narrative]) --> LCN[LoadCheckpointNode]
    LCN --> CVGN[CVGenerationNode]
    LCN --> CLN[CoverLetterNode]
    CVGN --> End1([CV Document])
    CLN --> End2([Cover Letter])
    
    subgraph LoadCheckpointNode
        Load[Load Edited Files]
    end
    
    subgraph CVGenerationNode
        Template1[Apply CV Template] --> Gen1[Generate Content]
    end
    
    subgraph CoverLetterNode
        Template2[Apply Letter Template] --> Gen2[Generate Content]
    end
```

## Data Flow Through Shared Store

```mermaid
flowchart TB
    subgraph Shared Store
        subgraph Input Data
            career_db[career_database]
            job_desc[job_description]
        end
        
        subgraph Extracted Data
            requirements[requirements]
            company_info[company_research]
        end
        
        subgraph Analysis Results
            mapping[requirement_mapping]
            strengths[strengths]
            gaps[gaps]
            score[suitability_score]
        end
        
        subgraph Strategy
            priorities[experience_priorities]
            narrative[narrative_strategy]
        end
        
        subgraph Output
            cv[generated_cv]
            letter[cover_letter]
        end
    end
    
    career_db -.-> mapping
    job_desc -.-> requirements
    requirements -.-> mapping
    mapping -.-> strengths
    mapping -.-> gaps
    company_info -.-> score
    strengths -.-> score
    gaps -.-> score
    score -.-> priorities
    priorities -.-> narrative
    narrative -.-> cv
    narrative -.-> letter
```

## Node Implementation Status

### Experience Database Building
| Node | Status | Dependencies |
|------|--------|--------------|
| ScanDocumentsNode | 🔴 Not Started | Google Drive API, File System |
| ExtractExperienceNode | 🔴 Not Started | PDF/Doc parsers |
| BuildDatabaseNode | 🔴 Not Started | Database Parser ✅ |

### Core Processing
| Node | Status | Dependencies |
|------|--------|--------------|
| ExtractRequirementsNode | 🔴 Not Started | LLM Wrapper ✅ |
| RequirementMappingNode | 🔴 Not Started | - |
| StrengthAssessmentNode | 🔴 Not Started | - |
| GapAnalysisNode | 🔴 Not Started | - |
| SuitabilityScoringNode | 🔴 Not Started | - |
| ExperiencePrioritizationNode | 🔴 Not Started | - |
| NarrativeStrategyNode | 🔴 Not Started | - |
| CVGenerationNode | 🔴 Not Started | - |
| CoverLetterNode | 🔴 Not Started | - |

### Company Research (AI Browser)
| Node | Status | Dependencies |
|------|--------|--------------|
| DecideActionNode | 🔴 Not Started | - |
| BrowserActionNode | 🔴 Not Started | Playwright/Puppeteer |
| SearchNode | 🔴 Not Started | AI Browser Tools |
| ExtractInfoNode | 🔴 Not Started | BeautifulSoup |
| CompanyAnalysisNode | 🔴 Not Started | LLM Wrapper ✅ |

### Workflow Management
| Node | Status | Dependencies |
|------|--------|--------------|
| SaveCheckpointNode | 🔴 Not Started | - |
| LoadCheckpointNode | 🔴 Not Started | - |

## Completed Components

✅ **Infrastructure**
- PocketFlow framework setup
- Career database schema (enhanced with projects)
- Database parser utility
- LLM wrapper (OpenRouter)

## Enhanced Career Database Schema

```mermaid
erDiagram
    PersonalInfo ||--|| CareerDB : contains
    Experience }|--|| CareerDB : contains
    Education }|--|| CareerDB : contains
    Skills ||--|| CareerDB : contains
    Projects }|--|| CareerDB : contains
    
    Experience ||--|{ ExperienceProjects : "has nested"
    
    Experience {
        string title
        string company
        string duration
        string location
        string description
        array achievements
        array technologies
        int team_size
        string reason_for_leaving
        array company_culture_pros
        array company_culture_cons
    }
    
    ExperienceProjects {
        string title
        string description
        array achievements
        string role
        array technologies
        array key_stakeholders
        array notable_challenges
        int direct_reports
        string reports_to
    }
    
    Projects {
        string name
        string type
        string description
        array technologies
        array outcomes
        string url
        string context
    }
```

## Next Implementation Priority

Based on the updated workflow, the implementation order should be:

1. **Experience Database Builder** (New Tasks)
   - ScanDocumentsNode for Google Drive and local files
   - ExtractExperienceNode with PDF/MD parsers
   - BuildDatabaseNode to structure the data
   - This provides the foundation for all subsequent flows

2. **Workflow Management Nodes** (New Tasks)
   - SaveCheckpointNode
   - LoadCheckpointNode
   - Essential for pause/resume functionality

3. **RequirementExtractionFlow** (Tasks 5-8)
   - Design requirements YAML schema
   - Implement ExtractRequirementsNode
   - Create prompt engineering
   - Wire up the flow

4. **AnalysisFlow with Checkpoints** (Tasks 9-12)
   - RequirementMappingNode
   - StrengthAssessmentNode
   - GapAnalysisNode
   - Integrate checkpoint saving

5. **AI-Browser Research Flow** (Updated Tasks 13-18)
   - Set up Playwright/Puppeteer
   - Implement AI browser agent
   - Create search and extraction nodes

This order ensures:

- Career database is populated first
- Pause/resume capability is available early
- Each stage can be tested independently
- User can review and edit at key points