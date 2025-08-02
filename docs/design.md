# PocketFlow Career Application Agent Design

## Overview

This system automates the customization of job applications using The-Pocket/PocketFlow framework - a minimalist 100-line LLM orchestration framework that models applications as directed graphs.

## Core Concepts

### 1. Nodes (Discrete Units of Work)

#### Work Experience Database Building
- **ScanDocumentsNode**: Scans Google Drive folders and local directories for documents
- **ExtractExperienceNode**: Extracts work experience from documents (PDFs, .md files, Google Docs)
- **BuildDatabaseNode**: Structures extracted data into career database format

#### Job Application Processing
- **ExtractRequirementsNode**: Parses job descriptions into structured requirements
- **RequirementMappingNode**: Maps candidate experience to job requirements  
- **StrengthAssessmentNode**: Evaluates candidate strengths
- **GapAnalysisNode**: Identifies missing qualifications

#### Company Research
- **DecideActionNode**: Determines research needs
- **BrowserActionNode**: Uses AI-driven headless browser for web interactions
- **SearchNode**: Performs Google searches and navigates results
- **ExtractInfoNode**: Extracts relevant company information
- **CompanyAnalysisNode**: Analyzes gathered company data

#### Assessment and Strategy
- **SuitabilityScoringNode**: Calculates fit score
- **ExperiencePrioritizationNode**: Ranks relevant experiences
- **NarrativeStrategyNode**: Develops application narrative

#### Document Generation
- **CVGenerationNode**: Creates tailored CV
- **CoverLetterNode**: Generates cover letter

#### User Review Nodes
- **SaveCheckpointNode**: Saves intermediate outputs for user review
- **LoadCheckpointNode**: Loads user-edited files to resume workflow

### 2. Flows (Directed Graphs)

- **ExperienceDatabaseFlow**: Builds/updates work experience database from documents
- **RequirementExtractionFlow**: Job parsing pipeline
- **AnalysisFlow**: Candidate evaluation pipeline (with pause for user review)
- **CompanyResearchFlow**: AI-browser-driven information gathering
- **AssessmentFlow**: Suitability scoring pipeline
- **NarrativeFlow**: Story development pipeline (with pause for user review)
- **GenerationFlow**: Document creation pipeline

### 3. Shared Store (Data Repository)

Central data store containing:

- Career database (candidate information)
- Job requirements
- Analysis results
- Research findings
- Generated documents
- Checkpoint files (for pause/resume)
- Document sources metadata

**Data Contract**: The complete shared store data contract is documented in [shared_store_data_contract.md](shared_store_data_contract.md), which defines:
- All keys and their data types
- Producer flows (which flow creates each data element)
- Consumer flows (which flows use each data element)
- Validation rules and constraints
- Required fields for each flow

The shared store serves as the central nervous system enabling communication between all phases, with strict type checking and validation to ensure data integrity.

## Data Flow

```txt
Document Sources → ExperienceDatabaseFlow → Career Database
(Google Drive, Local)                              ↓
                                                   ↓
Job Description → RequirementExtractionFlow → Structured Requirements
                                                        ↓
                        AnalysisFlow → Strengths/Gaps Analysis
                              ↓                        ↓
                        [User Review]           [checkpoint.yaml]
                              ↓
Company Name → CompanyResearchFlow → Company Insights
(AI Browser)                                ↓
                    AssessmentFlow → Suitability Score
                                          ↓
                     NarrativeFlow → Application Strategy
                              ↓                     ↓
                        [User Review]        [narrative.yaml]
                              ↓
                    GenerationFlow → CV + Cover Letter
```

## Workflow Management

### Pause/Resume Capability

The system supports pausing at key decision points for user review:

1. **After AnalysisFlow**: User reviews and edits strengths/gaps analysis
2. **After NarrativeFlow**: User reviews and edits narrative strategy

Each pause point:
- Saves current state to a checkpoint file (YAML format)
- Allows user to edit the output file
- Can resume from the checkpoint when ready

### Restart Capability

Users can restart the workflow from any major flow by providing:
- Required input files (e.g., `analysis_output.yaml` to start from AssessmentFlow)
- The system detects existing files and offers to skip completed steps

## Key Design Decisions

1. **Modular Architecture**: Each node handles one specific task
2. **Async Execution**: Nodes can run in parallel where dependencies allow
3. **YAML-based Data**: Human-readable configuration and outputs
4. **LLM Integration**: Nodes leverage language models for intelligent processing
5. **Extensibility**: Easy to add new nodes or modify flows
6. **User-in-the-Loop**: Critical outputs are reviewed by users before proceeding
7. **Flexible Entry Points**: Can start/restart from any major flow
8. **AI-Driven Browser**: Use AI agents for complex web interactions

## Technology Choices

### Document Processing
- **Google Drive API**: For accessing Google Docs
- **PyPDF2/pdfplumber**: For PDF extraction
- **Python-docx**: For Word documents
- **Markdown parser**: For .md files

### Web Research
- **Playwright/Puppeteer**: Headless browser automation
- **LangChain Browser Tools**: AI-driven browser interactions
- **BeautifulSoup**: HTML parsing
- **Requests**: Simple HTTP requests

### Data Persistence
- **YAML files**: For checkpoints and intermediate outputs
- **JSON**: For structured data exchange
- **SQLite**: Optional for career database storage

## Implementation Notes

- Following PocketFlow's minimalist philosophy
- Core framework files: nodes.py, flow.py, main.py
- Utilities isolated in utils/ directory
- Clear separation between orchestration and business logic
- Checkpoint files stored in `checkpoints/` directory
- User-editable outputs in `outputs/` directory
- Shared store validation enforced through `utils/shared_store_validator.py`
- Complete data contract defined in `docs/shared_store_data_contract.md`
