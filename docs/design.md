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

## System Architecture

### Core Components

#### 1. PocketFlow Base Classes (pocketflow.py)
- **Node**: Base class for all processing units
  - `prep()`: Read from shared store
  - `exec()`: Execute computation (often LLM calls)
  - `post()`: Write results and return action
- **BatchNode**: Parallel processing for collections
- **Flow**: Orchestrates nodes in directed graphs
- **BatchFlow**: Parallel flow execution

#### 2. Application Nodes (nodes.py)
Organized into functional categories:

**Document Processing**
- ScanDocumentsNode: Document discovery
- ExtractExperienceNode: Work experience extraction
- BuildDatabaseNode: Career database construction

**Requirements Analysis**
- ExtractRequirementsNode: Job parsing
- RequirementMappingNode: Experience mapping
- StrengthAssessmentNode: Strength evaluation
- GapAnalysisNode: Gap identification

**Company Research**
- DecideActionNode: Research planning
- WebSearchNode: Search execution
- ReadContentNode: Content extraction
- SynthesizeInfoNode: Information synthesis

**Strategy & Generation**
- SuitabilityScoringNode: Fit calculation
- ExperiencePrioritizationNode: Experience ranking
- NarrativeStrategyNode: Story development
- CVGenerationNode: CV creation
- CoverLetterNode: Cover letter writing

**Workflow Management**
- SaveCheckpointNode: State persistence
- LoadCheckpointNode: State recovery

#### 3. Flow Orchestration (flow.py)
- ExperienceDatabaseFlow: Document → Database pipeline
- RequirementExtractionFlow: Job → Requirements
- AnalysisFlow: Requirements → Analysis (with checkpoint)
- CompanyResearchAgent: Autonomous research loop
- AssessmentFlow: Scoring pipeline
- NarrativeFlow: Strategy development (with checkpoint)
- GenerationFlow: Document generation

#### 4. Utilities (utils/)
- **llm_wrapper.py**: LLM abstraction layer
- **career_database_parser.py**: Database I/O
- **document_scanner.py**: File discovery
- **shared_store_validator.py**: Data validation
- **web_tools.py**: Web scraping utilities

### Data Architecture

#### Career Database Schema
Defined in `docs/career_database_schema.md`:
```yaml
personal_info:
  name: string
  email: string
  phone: string (optional)
  location: string (optional)
  
work_experience:
  - company: string
    title: string
    start_date: YYYY-MM
    end_date: YYYY-MM or null
    responsibilities: [string]
    achievements:
      - description: string
        metrics: [string]
    technologies: [string]
    projects:
      - name: string
        role: string
        description: string
        technologies: [string]
        outcomes: [string]
```

#### Job Requirements Schema
Defined in `docs/job_requirements_schema.md`:
```yaml
job_info:
  title: string
  company: string
  location: string
  
requirements:
  required:
    technical_skills: [string]
    experience_years: number
    qualifications: [string]
  preferred:
    technical_skills: [string]
    qualifications: [string]
```

### Error Handling Strategy

1. **Node-Level Retry**: Built into Node base class
2. **Graceful Degradation**: Continue with partial data
3. **User Notification**: Clear error messages
4. **Checkpoint Recovery**: Resume from last good state
5. **Validation Errors**: Detailed field-level feedback

### Security Considerations

1. **API Key Management**: Environment variables
2. **File Access**: Sandboxed to project directories
3. **Web Scraping**: Rate limiting and robots.txt compliance
4. **Data Privacy**: No PII in logs or checkpoints
5. **Input Validation**: Schema validation for all inputs

### Performance Optimization

1. **Parallel Processing**: BatchNode for document analysis
2. **Caching**: LLM response caching in development
3. **Lazy Loading**: Documents processed on-demand
4. **Incremental Updates**: Merge with existing database
5. **Checkpoint Efficiency**: Only save changed data

### Testing Strategy

Documented in `docs/testing_strategy.md`:
1. **Unit Tests**: Individual node validation
2. **Integration Tests**: Flow execution
3. **Mock LLM**: Deterministic testing
4. **Schema Validation**: Input/output contracts
5. **Documentation Tests**: Code examples validation
