---
id: task-43
title: Implement LoadCheckpointNode
status: completed
assignee:
  - unassigned
created_date: ''
updated_date: '2025-08-03'
labels: []
dependencies:
  - task-42
priority: medium
---

## Description

Implement the LoadCheckpointNode that loads previously saved checkpoints and user-edited files to resume workflow execution.

## Acceptance Criteria

- [ ] Loads checkpoint files from specified location
- [ ] Validates checkpoint integrity and version
- [ ] Merges user-edited files with checkpoint data
- [ ] Handles missing or corrupted files gracefully
- [ ] Supports multiple checkpoint formats
- [ ] Detects and reports user modifications
- [ ] Can skip to specific workflow stage

## Technical Details

- Extends base Node class
- Reads from `checkpoints/` and `outputs/` directories
- Validates against expected schema
- Merge strategy:
  - User edits take precedence
  - Preserve unedited checkpoint data
  - Log all modifications
- Supports workflow branching based on checkpoint
- Sets flow state for proper resumption

## Implementation Plan

### Node Structure

```python
class LoadCheckpointNode(Node):
    """Loads workflow state from checkpoint and user edits."""
    
    def __init__(self, checkpoint_name: str = None, auto_detect: bool = True):
        self.checkpoint_name = checkpoint_name
        self.auto_detect = auto_detect
        self.checkpoint_dir = Path("checkpoints")
        self.output_dir = Path("outputs")
        
    def prep(self, shared: dict) -> dict:
        """Prepare to load checkpoint."""
        # Find checkpoint file
        if self.checkpoint_name:
            checkpoint_path = self.find_checkpoint(self.checkpoint_name)
        elif self.auto_detect:
            checkpoint_path = self.find_latest_checkpoint(shared.get("flow_name"))
        else:
            raise ValueError("No checkpoint specified")
            
        return {
            "checkpoint_path": checkpoint_path,
            "flow_name": shared.get("flow_name", "unknown")
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Load checkpoint and merge with user edits."""
        # Load checkpoint
        checkpoint_data = self.load_checkpoint(prep_res["checkpoint_path"])
        
        # Validate checkpoint
        self.validate_checkpoint(checkpoint_data)
        
        # Find and load user edits
        user_edits = self.load_user_edits(checkpoint_data)
        
        # Merge data
        merged_state = self.merge_checkpoint_and_edits(checkpoint_data, user_edits)
        
        # Detect modifications
        modifications = self.detect_modifications(checkpoint_data, merged_state)
        
        return {
            "merged_state": merged_state,
            "modifications": modifications,
            "checkpoint_metadata": checkpoint_data.get("metadata", {}),
            "recovery_info": checkpoint_data.get("recovery_info", {})
        }
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Update shared store with loaded state."""
        # Merge loaded state into shared
        shared.update(exec_res["merged_state"])
        
        # Add metadata
        shared["resumed_from_checkpoint"] = {
            "checkpoint_name": exec_res["checkpoint_metadata"].get("checkpoint_name"),
            "timestamp": exec_res["checkpoint_metadata"].get("timestamp"),
            "modifications": exec_res["modifications"]
        }
        
        # Log resumption
        print(f"\n✓ Resumed from checkpoint: {prep_res['checkpoint_path'].name}")
        if exec_res["modifications"]:
            print(f"  Found {len(exec_res['modifications'])} user modifications")
        
        # Determine next action based on recovery info
        next_action = exec_res["recovery_info"].get("next_action", "continue")
        return next_action
```

### Checkpoint Discovery

```python
def find_latest_checkpoint(self, flow_name: str) -> Path:
    """Find the most recent checkpoint for a flow."""
    # Check for latest symlink first
    latest_link = self.checkpoint_dir / f"{flow_name}_latest.yaml"
    if latest_link.exists():
        return latest_link.resolve()
    
    # Find all checkpoints for this flow
    pattern = f"{flow_name}_*.yaml"
    checkpoints = list(self.checkpoint_dir.glob(pattern))
    
    if not checkpoints:
        raise FileNotFoundError(f"No checkpoints found for flow: {flow_name}")
    
    # Return most recent
    return max(checkpoints, key=lambda p: p.stat().st_mtime)

def find_checkpoint(self, checkpoint_name: str) -> Path:
    """Find a specific checkpoint by name."""
    # Try exact match
    checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.yaml"
    if checkpoint_path.exists():
        return checkpoint_path
    
    # Try with wildcards
    pattern = f"*{checkpoint_name}*.yaml"
    matches = list(self.checkpoint_dir.glob(pattern))
    
    if not matches:
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_name}")
    
    if len(matches) > 1:
        # Return most recent if multiple matches
        return max(matches, key=lambda p: p.stat().st_mtime)
    
    return matches[0]
```

### User Edit Detection

```python
def load_user_edits(self, checkpoint_data: dict) -> dict:
    """Load user-edited files associated with checkpoint."""
    edits = {}
    
    # Get export paths from checkpoint
    last_checkpoint = checkpoint_data.get("shared_state", {}).get("last_checkpoint", {})
    export_paths = last_checkpoint.get("exports", [])
    
    for export_path in export_paths:
        path = Path(export_path)
        if path.exists():
            # Load edited file
            with open(path, 'r') as f:
                content = yaml.safe_load(f)
            
            # Extract field name from path
            field_name = path.stem.replace("_review", "").replace("_edited", "")
            edits[field_name] = content
    
    return edits

def detect_modifications(self, original: dict, modified: dict) -> List[dict]:
    """Detect what the user changed."""
    modifications = []
    
    def compare_values(path: str, orig: Any, mod: Any):
        if orig != mod:
            modifications.append({
                "path": path,
                "original": orig,
                "modified": mod,
                "type": type(mod).__name__
            })
    
    # Deep comparison of data structures
    def deep_compare(path: str, orig: dict, mod: dict):
        all_keys = set(orig.keys()) | set(mod.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            if key not in orig:
                modifications.append({
                    "path": new_path,
                    "action": "added",
                    "value": mod[key]
                })
            elif key not in mod:
                modifications.append({
                    "path": new_path,
                    "action": "deleted",
                    "value": orig[key]
                })
            elif isinstance(orig[key], dict) and isinstance(mod[key], dict):
                deep_compare(new_path, orig[key], mod[key])
            else:
                compare_values(new_path, orig[key], mod[key])
    
    deep_compare("", original.get("shared_state", {}), modified)
    
    return modifications
```

### Merge Strategy

```python
def merge_checkpoint_and_edits(self, checkpoint: dict, edits: dict) -> dict:
    """Merge checkpoint data with user edits."""
    # Start with checkpoint state
    merged = checkpoint.get("shared_state", {}).copy()
    
    # Apply user edits
    for field_name, edited_content in edits.items():
        if field_name in merged:
            # Replace with edited version
            merged[field_name] = edited_content
        else:
            # Add new field
            merged[field_name] = edited_content
    
    # Preserve checkpoint metadata
    merged["checkpoint_metadata"] = checkpoint.get("metadata", {})
    
    return merged
```

### Validation

```python
def validate_checkpoint(self, checkpoint_data: dict) -> None:
    """Validate checkpoint integrity and compatibility."""
    # Check format version
    metadata = checkpoint_data.get("metadata", {})
    version = metadata.get("format_version", "0.0")
    
    if not self.is_version_compatible(version):
        raise ValueError(f"Incompatible checkpoint version: {version}")
    
    # Validate required fields
    required_fields = ["metadata", "shared_state"]
    for field in required_fields:
        if field not in checkpoint_data:
            raise ValueError(f"Invalid checkpoint: missing {field}")
    
    # Validate timestamp
    timestamp_str = metadata.get("timestamp")
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age_days = (datetime.now() - timestamp).days
            if age_days > 30:
                print(f"Warning: Checkpoint is {age_days} days old")
        except ValueError:
            print("Warning: Invalid timestamp in checkpoint")
```

## Dependencies

- YAML parsing
- File system operations
- Schema validation
- Base Node class

## Testing Requirements

- Test checkpoint loading
- Test user edit detection
- Test corruption handling
- Test version compatibility
- Test merge strategies
- Test workflow resumption

## Error Handling

1. **Missing Checkpoints**
   - Clear error message
   - Suggest creating new checkpoint
   - List available checkpoints

2. **Corrupted Files**
   - Attempt recovery from backup
   - Log corruption details
   - Provide manual recovery steps

3. **Version Mismatch**
   - Attempt migration if possible
   - Warn about compatibility
   - Provide upgrade instructions

## Integration Notes

- Works with SaveCheckpointNode
- Enables pause/resume workflows
- Supports manual intervention
- Maintains workflow continuity

## Future Enhancements

- Checkpoint migration tools
- Diff visualization for edits
- Automatic backup validation
- Cloud checkpoint storage
- Checkpoint merging from multiple sources
