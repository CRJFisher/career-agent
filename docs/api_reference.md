# API Reference

Complete reference for all nodes and flows in the Career Application Agent.

## Table of Contents

1. [Base Classes](#base-classes)
2. [Document Processing Nodes](#document-processing-nodes)
3. [Requirements Analysis Nodes](#requirements-analysis-nodes)
4. [Company Research Nodes](#company-research-nodes)
5. [Strategy & Generation Nodes](#strategy--generation-nodes)
6. [Workflow Management Nodes](#workflow-management-nodes)
7. [Flows](#flows)
8. [Utilities](#utilities)

## Base Classes

### Node

Base class for all processing units.

```python
class Node:
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data from shared store."""
        pass
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """Execute computation (often LLM calls)."""
        pass
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> str:
        """Update shared store and return action."""
        pass
```

### BatchNode

Extends Node for parallel processing of collections.

```python
class BatchNode(Node):
    def exec(self, items: List[Dict]) -> List[Dict]:
        """Process multiple items in parallel."""
        pass
```

## Document Processing Nodes

### ScanDocumentsNode

Scans configured sources for work experience documents.

**Input (shared store)**:
- `scan_config`: Configuration for document sources

**Output (shared store)**:
- `document_sources`: List of discovered documents
- `scan_errors`: Any errors during scanning

**Example**:
```python
shared = {
    "scan_config": {
        "local_directories": ["/home/user/documents"],
        "google_drive_folders": ["Career Documents"],
        "file_types": [".pdf", ".docx", ".md"]
    }
}
```

### ExtractExperienceNode

Extracts work experience from documents using LLM analysis.

**Input (shared store)**:
- `document_sources`: List of documents to process
- `extraction_mode`: "comprehensive" or "quick"

**Output (shared store)**:
- `extracted_experiences`: List of extracted work experiences
- `extraction_summary`: Statistics about extraction

### BuildDatabaseNode

Structures extracted experiences into career database format.

**Input (shared store)**:
- `extracted_experiences`: Raw extracted experiences
- `existing_career_database`: Optional existing database to merge

**Output (shared store)**:
- `career_database`: Structured career database
- `build_summary`: Deduplication and validation results

## Requirements Analysis Nodes

### ExtractRequirementsNode

Parses job descriptions to extract structured requirements.

**Input (shared store)**:
- `job_description`: Raw job description text

**Output (shared store)**:
- `requirements`: Structured job requirements

**Schema**:
```yaml
requirements:
  job_info:
    title: string
    company: string
    location: string
  required:
    technical_skills: [string]
    experience_years: number
    qualifications: [string]
  preferred:
    technical_skills: [string]
    qualifications: [string]
```

### RequirementMappingNode

Maps candidate experience to job requirements.

**Input (shared store)**:
- `requirements`: Job requirements
- `career_db`: Career database

**Output (shared store)**:
- `requirement_mapping_raw`: Initial mappings with evidence

### StrengthAssessmentNode

Evaluates the strength of requirement mappings.

**Input (shared store)**:
- `requirement_mapping_raw`: Raw mappings

**Output (shared store)**:
- `requirement_mapping_assessed`: Mappings with strength ratings (HIGH/MEDIUM/LOW)

### GapAnalysisNode

Identifies missing qualifications and suggests mitigations.

**Input (shared store)**:
- `requirements`: Job requirements
- `requirement_mapping_assessed`: Assessed mappings

**Output (shared store)**:
- `gaps`: List of gaps with mitigation strategies
- `coverage_score`: Overall requirement coverage percentage

## Company Research Nodes

### DecideActionNode

Cognitive core for research agent - decides next research action.

**Input (shared store)**:
- `company_name`: Company to research
- `research_state`: Current research progress

**Output (shared store)**:
- Action decision: "web_search", "read_content", "synthesize", or "finish"

### WebSearchNode

Performs web searches for company information.

**Input (shared store)**:
- `search_query`: Query to search

**Output (shared store)**:
- `search_results`: List of relevant URLs and snippets

### ReadContentNode

Extracts content from web pages.

**Input (shared store)**:
- `url`: URL to read

**Output (shared store)**:
- `page_content`: Extracted and cleaned content

### SynthesizeInfoNode

Synthesizes gathered information into structured insights.

**Input (shared store)**:
- `research_state`: All gathered information

**Output (shared store)**:
- `company_research`: Structured company insights

## Strategy & Generation Nodes

### SuitabilityScoringNode

Calculates candidate-job fit scores.

**Input (shared store)**:
- `requirement_mapping_final`: Final requirement mappings
- `gaps`: Identified gaps
- `company_research`: Company insights

**Output (shared store)**:
- `suitability_assessment`: Technical and cultural fit scores

### ExperiencePrioritizationNode

Ranks experiences by relevance to the position.

**Input (shared store)**:
- `career_db`: Career database
- `requirements`: Job requirements
- `suitability_assessment`: Fit assessment

**Output (shared store)**:
- `prioritized_experiences`: Ranked experiences with relevance scores

### NarrativeStrategyNode

Develops application narrative strategy.

**Input (shared store)**:
- `prioritized_experiences`: Ranked experiences
- `suitability_assessment`: Fit assessment
- `requirements`: Job requirements

**Output (shared store)**:
- `narrative_strategy`: Career arc, key messages, evidence stories

### CVGenerationNode

Creates tailored CV based on strategy.

**Input (shared store)**:
- `career_db`: Career database
- `narrative_strategy`: Application strategy
- `prioritized_experiences`: Relevant experiences

**Output (shared store)**:
- `cv_markdown`: Generated CV in markdown format

### CoverLetterNode

Generates personalized cover letter.

**Input (shared store)**:
- `narrative_strategy`: Application strategy
- `company_research`: Company insights
- `suitability_assessment`: Fit assessment

**Output (shared store)**:
- `cover_letter_text`: Generated cover letter

## Workflow Management Nodes

### SaveCheckpointNode

Saves workflow state for user review.

**Parameters**:
- `flow_name`: Name of the flow creating checkpoint
- `checkpoint_data`: Fields to save
- `user_message`: Custom instructions for user

**Example**:
```python
node = SaveCheckpointNode()
node.set_params({
    "flow_name": "analysis",
    "checkpoint_data": ["requirements", "gaps"],
    "user_message": "Review and edit the analysis"
})
```

### LoadCheckpointNode

Loads checkpoint and merges user edits.

**Parameters**:
- `checkpoint_name`: Specific checkpoint to load
- `auto_detect`: Find latest checkpoint automatically

**Features**:
- Detects user modifications
- Validates checkpoint integrity
- Merges edits with checkpoint data

## Flows

### ExperienceDatabaseFlow

Builds career database from documents.

```python
flow = ExperienceDatabaseFlow(config={
    "scan_config": {...},
    "output_path": "career_database.yaml",
    "enable_checkpoints": True
})
```

**Pipeline**:
1. ScanDocumentsNode
2. ExtractExperienceNode (parallel)
3. BuildDatabaseNode

### RequirementExtractionFlow

Extracts requirements from job description.

```python
flow = RequirementExtractionFlow()
shared = {"job_description": "..."}
flow.run(shared)
```

### AnalysisFlow

Analyzes candidate fit with checkpoint.

**Pipeline**:
1. RequirementMappingNode
2. StrengthAssessmentNode
3. GapAnalysisNode
4. SaveCheckpointNode (pause for review)

### CompanyResearchAgent

Autonomous research loop using DecideActionNode.

```python
flow = CompanyResearchAgent(max_iterations=20)
shared = {"company_name": "TechCorp"}
flow.run(shared)
```

### NarrativeFlow

Develops application strategy with checkpoint.

**Pipeline**:
1. ExperiencePrioritizationNode
2. NarrativeStrategyNode
3. SaveCheckpointNode (pause for review)

### GenerationFlow

Creates final application documents.

**Pipeline**:
1. LoadCheckpointNode (resume from narrative)
2. CVGenerationNode + CoverLetterNode (parallel)

## Utilities

### LLM Wrapper

```python
from utils.llm_wrapper import get_default_llm_wrapper

llm = get_default_llm_wrapper()
response = llm.generate(
    prompt="Extract requirements from: ...",
    max_tokens=2000,
    temperature=0.3
)
```

### Document Scanner

```python
from utils.document_scanner import scan_documents

documents = scan_documents(
    local_dirs=["/path/to/docs"],
    file_types=[".pdf", ".docx"],
    google_drive_folders=["Career"]
)
```

### Career Database Parser

```python
from utils.career_database_parser import (
    load_career_database,
    save_career_database,
    validate_career_database
)

# Load and validate
db = load_career_database("career.yaml")
errors = validate_career_database(db)

# Save
save_career_database(db, "career_updated.yaml")
```

### Shared Store Validator

```python
from utils.shared_store_validator import validate_shared_store

errors = validate_shared_store(shared, flow_name="analysis")
if errors:
    raise ValueError(f"Validation failed: {errors}")
```

## Error Handling

All nodes support retry logic:

```python
class MyNode(Node):
    def __init__(self):
        super().__init__(max_retries=3, wait=1.0)
```

Common error patterns:
- `FileNotFoundError`: Missing input files
- `ValueError`: Invalid data format
- `RuntimeError`: LLM or external service errors

## Best Practices

1. **Always validate inputs** in `prep()` method
2. **Handle partial failures** gracefully
3. **Log important operations** for debugging
4. **Use type hints** for clarity
5. **Write comprehensive tests** for new nodes

## Examples

### Creating a Custom Node

```python
class CustomAnalysisNode(Node):
    """Performs custom analysis on career data."""
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        # Validate required inputs
        if "career_db" not in shared:
            raise ValueError("career_db required")
        
        return {
            "career_db": shared["career_db"],
            "config": shared.get("analysis_config", {})
        }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        # Perform analysis
        career_db = prep_res["career_db"]
        
        # LLM call example
        llm = get_default_llm_wrapper()
        analysis = llm.generate(
            prompt=f"Analyze career: {career_db}",
            max_tokens=1000
        )
        
        return {"analysis": analysis}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict, exec_res: Dict) -> str:
        # Store results
        shared["custom_analysis"] = exec_res["analysis"]
        return "continue"
```

### Creating a Custom Flow

```python
class CustomFlow(Flow):
    """Custom analysis workflow."""
    
    def __init__(self):
        # Create nodes
        extract = ExtractRequirementsNode()
        analyze = CustomAnalysisNode()
        
        # Connect nodes
        extract >> analyze
        
        # Initialize flow
        super().__init__(start=extract)
```