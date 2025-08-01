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