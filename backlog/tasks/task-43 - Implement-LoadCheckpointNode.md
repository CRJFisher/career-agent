# Task: Implement LoadCheckpointNode

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