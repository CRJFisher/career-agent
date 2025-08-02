---
id: task-42
title: Implement SaveCheckpointNode
status: pending
priority: medium
assignee: unassigned
created: 2024-01-01
updated: 2025-08-02
tags: [node, checkpoint, persistence, pocketflow]
dependencies: []
estimated_hours: 3
actual_hours: 0
---

# Task: Implement SaveCheckpointNode

## Description

Implement the SaveCheckpointNode that saves workflow state and outputs to files for user review, enabling pause/resume functionality.

## Acceptance Criteria

- [ ] Saves current shared store state to checkpoint file
- [ ] Exports specific outputs to user-editable YAML files
- [ ] Creates human-readable output with comments
- [ ] Preserves data types and structure
- [ ] Generates notification for user review
- [ ] Supports different output formats per flow
- [ ] Creates backup of previous checkpoint

## Technical Details

- Extends base Node class
- Saves to `checkpoints/` directory with timestamp
- Exports to `outputs/` directory for user editing
- File naming convention: `{flow_name}_{timestamp}.yaml`
- Includes metadata:
  - Timestamp
  - Flow name and state
  - Node that created checkpoint
  - Instructions for user
- Configurable fields to export per flow

## Implementation Plan

### Node Structure

```python
class SaveCheckpointNode(Node):
    """Saves workflow state for pause/resume and user review."""
    
    def __init__(self, checkpoint_name: str, export_config: dict = None):
        self.checkpoint_name = checkpoint_name
        self.export_config = export_config or {}
        self.checkpoint_dir = Path("checkpoints")
        self.output_dir = Path("outputs")
        
    def prep(self, shared: dict) -> dict:
        """Prepare checkpoint data."""
        return {
            "checkpoint_name": self.checkpoint_name,
            "flow_name": shared.get("flow_name", "unknown"),
            "timestamp": datetime.now(),
            "shared_state": shared.copy(),
            "export_fields": self.export_config.get("fields", [])
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Save checkpoint and export user files."""
        # Create directories
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Save checkpoint
        checkpoint_path = self.save_checkpoint(prep_res)
        
        # Export user-editable files
        export_paths = self.export_user_files(prep_res)
        
        # Create summary
        summary = self.create_summary(checkpoint_path, export_paths)
        
        return {
            "checkpoint_path": checkpoint_path,
            "export_paths": export_paths,
            "summary": summary
        }
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Update shared store with checkpoint info."""
        shared["last_checkpoint"] = {
            "name": self.checkpoint_name,
            "path": exec_res["checkpoint_path"],
            "timestamp": prep_res["timestamp"].isoformat(),
            "exports": exec_res["export_paths"]
        }
        
        # Notify user
        print(f"\n✓ Checkpoint saved: {self.checkpoint_name}")
        print(f"  Review/edit files in: {self.output_dir}")
        
        return "continue"
```

### Checkpoint File Format

```yaml
# Checkpoint file: checkpoints/experience_extraction_2024-01-15T10-30-00.yaml
---
metadata:
  checkpoint_name: "extraction_complete"
  flow_name: "experience_database_flow"
  timestamp: "2024-01-15T10:30:00"
  node_class: "SaveCheckpointNode"
  format_version: "1.0"

shared_state:
  document_sources:
    - path: "/path/to/resume.pdf"
      type: ".pdf"
      # ... full document metadata
  
  extracted_experiences:
    - company: "Tech Corp"
      title: "Senior Engineer"
      # ... full experience data
  
  flow_config:
    # ... original configuration
  
  processing_stats:
    documents_scanned: 42
    experiences_extracted: 12
    # ... other statistics

recovery_info:
  next_node: "BuildDatabaseNode"
  can_resume: true
  required_state_keys:
    - "extracted_experiences"
    - "flow_config"
```

### User Export Format

```yaml
# User-editable file: outputs/extracted_experiences_review.yaml
# Generated: 2024-01-15 10:30:00
# 
# INSTRUCTIONS:
# 1. Review the extracted experiences below
# 2. Fix any errors or add missing information
# 3. Save this file when complete
# 4. Resume the workflow to continue processing
#
# Tips:
# - Dates should be in YYYY-MM format
# - Leave end_date empty for current positions
# - Add achievements with measurable results
---

experiences:
  - company: "Tech Corp"
    title: "Senior Software Engineer"
    start_date: "2020-01"
    end_date: null  # Current position
    
    # Add or edit responsibilities
    responsibilities:
      - "Led team of 5 engineers"
      - "Architected microservices platform"
    
    # Add measurable achievements
    achievements:
      - description: "Reduced API latency"
        metrics: ["40% improvement", "100ms to 60ms"]
    
    # Projects within this role
    projects:
      - name: "Platform Redesign"
        role: "Tech Lead"
        description: "Complete overhaul of legacy system"
        technologies: ["Python", "Kubernetes", "React"]
        # Add project outcomes
        outcomes:
          - "Improved scalability 10x"
          - "Reduced operational costs 30%"

# Add more experiences as needed...
```

### Export Configuration

```python
EXPORT_CONFIGS = {
    "experience_extraction": {
        "fields": ["extracted_experiences"],
        "template": "experience_review_template.yaml",
        "instructions": "Review and correct extracted work experiences"
    },
    
    "requirements_analysis": {
        "fields": ["job_requirements", "requirement_matches"],
        "template": "requirements_review_template.yaml",
        "instructions": "Verify job requirements and matches"
    },
    
    "narrative_strategy": {
        "fields": ["narrative_themes", "experience_priorities"],
        "template": "narrative_review_template.yaml",
        "instructions": "Review narrative strategy selections"
    }
}
```

### Backup Strategy

```python
def save_checkpoint(self, data: dict) -> Path:
    """Save checkpoint with backup."""
    timestamp = data["timestamp"].strftime("%Y%m%d_%H%M%S")
    filename = f"{data['flow_name']}_{timestamp}.yaml"
    checkpoint_path = self.checkpoint_dir / filename
    
    # Backup existing checkpoint if any
    latest_link = self.checkpoint_dir / f"{data['flow_name']}_latest.yaml"
    if latest_link.exists():
        backup_path = latest_link.with_suffix('.yaml.bak')
        shutil.copy2(latest_link, backup_path)
    
    # Save new checkpoint
    with open(checkpoint_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    # Update latest link
    if latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(checkpoint_path)
    
    return checkpoint_path
```

## Dependencies

- YAML serialization
- File system operations
- Base Node class

## Testing Requirements

- Test checkpoint file creation
- Test data serialization accuracy
- Test backup functionality
- Test with various data types
- Verify user-editable format
- Test file permissions and access

## Error Handling

1. **File System Errors**
   - Create directories if missing
   - Handle permission errors gracefully
   - Fallback to temp directory if needed

2. **Serialization Errors**
   - Handle non-serializable objects
   - Convert complex types to strings
   - Log warnings for data loss

3. **Backup Failures**
   - Continue without backup if needed
   - Log backup failures
   - Maintain checkpoint integrity

## Integration Notes

- Used by all major flows for pause/resume
- Configurable per flow requirements
- Supports manual intervention workflows
- Enables debugging and inspection

## Future Enhancements

- Compression for large checkpoints
- Encryption for sensitive data
- Cloud backup support
- Checkpoint versioning
- Automatic cleanup of old checkpoints