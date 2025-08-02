---
id: task-41
title: Implement ExperienceDatabaseFlow
status: pending
priority: high
assignee: unassigned
created: 2024-01-01
updated: 2025-08-02
tags: [flow, orchestration, experience-database, pocketflow]
dependencies: [task-38, task-39, task-40]
estimated_hours: 4
actual_hours: 0
---

## Description

Implement the ExperienceDatabaseFlow that orchestrates the complete process of building a career database from document sources.

## Acceptance Criteria

- [ ] Flow connects all experience database nodes in sequence
- [ ] Handles configuration for document sources
- [ ] Provides progress updates throughout the process
- [ ] Saves intermediate results for debugging
- [ ] Can be run independently or as part of main workflow
- [ ] Supports incremental updates to existing database
- [ ] Generates summary report of extraction process

## Technical Details

- Create flow connecting:
  1. ScanDocumentsNode
  2. ExtractExperienceNode  
  3. BuildDatabaseNode
- Implements error handling and retry logic
- Saves checkpoint after each major step
- Configuration includes:
  - Source locations (Google Drive, local)
  - Output path for career database
  - Extraction options (date ranges, etc.)
- Can merge with existing career database

## Implementation Plan

### Flow Structure

```python
class ExperienceDatabaseFlow:
    """Orchestrates career database building from documents."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.checkpoints_enabled = self.config.get("enable_checkpoints", True)
        self.checkpoint_dir = self.config.get("checkpoint_dir", ".checkpoints")
        
    def create_flow(self) -> Flow:
        """Create the experience database extraction flow."""
        # Initialize nodes
        scan_node = ScanDocumentsNode()
        extract_node = ExtractExperienceNode()
        build_node = BuildDatabaseNode()
        
        # Create flow
        flow = Flow(start=scan_node)
        
        # Connect nodes
        scan_node >> extract_node >> build_node
        
        # Add checkpoint nodes if enabled
        if self.checkpoints_enabled:
            save_scan = SaveCheckpointNode("scan_complete")
            save_extract = SaveCheckpointNode("extract_complete")
            
            scan_node >> save_scan >> extract_node
            extract_node >> save_extract >> build_node
        
        return flow
    
    async def run(self, shared_store: dict = None) -> dict:
        """Run the complete experience database flow."""
        # Initialize shared store
        shared = shared_store or {}
        
        # Add configuration
        shared.update({
            "scan_config": self.config.get("scan_config", {}),
            "extraction_config": self.config.get("extraction_config", {}),
            "database_output_path": self.config.get("output_path", "career_database.yaml"),
            "existing_career_database": self.load_existing_database()
        })
        
        # Check for resume from checkpoint
        if self.checkpoints_enabled:
            shared = self.resume_from_checkpoint(shared)
        
        # Create and run flow
        flow = self.create_flow()
        result = await flow.run(shared)
        
        # Generate final report
        self.generate_report(result)
        
        return result
```

### Configuration Schema

```yaml
experience_database_config:
  scan_config:
    google_drive_folders:
      - folder_id: "1234567890"
        name: "Career Documents"
      - folder_id: "0987654321"
        name: "Project Archives"
    local_directories:
      - "~/Documents/Work Experience"
      - "~/Projects/Portfolio"
    file_types: [".pdf", ".docx", ".md"]
    date_filter:
      min_date: "2020-01-01"
  
  extraction_config:
    batch_size: 5
    llm_model: "gpt-4"
    confidence_threshold: 0.8
    extract_projects: true
    extract_culture_fit: true
  
  output_path: "./career_database.yaml"
  enable_checkpoints: true
  checkpoint_dir: "./.checkpoints"
  merge_with_existing: true
```

### Progress Tracking

```python
class ProgressTracker:
    """Track and report flow progress."""
    
    def __init__(self):
        self.stages = {
            "scanning": {"status": "pending", "progress": 0},
            "extracting": {"status": "pending", "progress": 0},
            "building": {"status": "pending", "progress": 0}
        }
    
    def update(self, stage: str, status: str, progress: int = None):
        """Update stage progress."""
        self.stages[stage]["status"] = status
        if progress:
            self.stages[stage]["progress"] = progress
        self.report()
    
    def report(self):
        """Display current progress."""
        print("\n=== Experience Database Flow Progress ===")
        for stage, info in self.stages.items():
            status = info["status"]
            progress = info["progress"]
            print(f"{stage.capitalize()}: {status} ({progress}%)")
```

### Error Recovery

```python
def handle_node_error(node_name: str, error: Exception, shared: dict) -> str:
    """Handle errors during flow execution."""
    
    # Log error
    logger.error(f"Error in {node_name}: {error}")
    
    # Save error state
    shared.setdefault("errors", []).append({
        "node": node_name,
        "error": str(error),
        "timestamp": datetime.now().isoformat()
    })
    
    # Determine recovery action
    if node_name == "ScanDocumentsNode":
        # Critical - cannot continue without documents
        return "abort"
    elif node_name == "ExtractExperienceNode":
        # Can continue with partial extraction
        return "continue"
    else:
        # Try to continue
        return "continue"
```

### Summary Report

```yaml
experience_database_summary:
  flow_status: "completed"
  duration_minutes: 15.5
  
  scanning_phase:
    sources_scanned: 5
    documents_found: 42
    total_size_mb: 125.3
    errors: []
  
  extraction_phase:
    documents_processed: 42
    experiences_extracted: 12
    projects_found: 28
    extraction_rate: 1.0
    errors: []
  
  building_phase:
    experiences_before_dedup: 12
    experiences_after_dedup: 8
    projects_total: 25
    validation_passed: true
    database_saved: "./career_database.yaml"
  
  quality_metrics:
    high_confidence_extractions: 38
    medium_confidence_extractions: 4
    low_confidence_extractions: 0
    
  next_steps:
    - "Review extracted experiences for accuracy"
    - "Add any missing experiences manually"
    - "Run main application flow with new database"
```

## Dependencies

- All experience database nodes (tasks 38-40)
- Base Flow class implementation

## Testing Requirements

- Test full flow with sample documents
- Test incremental updates
- Test error recovery
- Test with various document sources
- Verify output matches expected schema
- Test checkpoint/resume functionality

## Integration Points

- Can be run standalone via CLI
- Integrated into main application workflow
- Supports programmatic invocation
- Results feed into job application flow

## Performance Optimization

- Parallel document scanning where possible
- Batch processing for extraction
- Incremental updates to avoid full rebuilds
- Caching of parsed documents

## Future Enhancements

- Real-time progress UI
- Support for more document sources
- Machine learning for better extraction
- Version control for career database
- Automatic scheduling for updates