# Task: Implement ScanDocumentsNode

## Description
Implement the ScanDocumentsNode that discovers and lists all relevant documents from configured Google Drive folders and local directories for work experience extraction.

## Acceptance Criteria
- [ ] Node reads configuration for source locations from shared store
- [ ] Scans Google Drive folders using document scanning utility
- [ ] Scans local directories for relevant files
- [ ] Filters out non-relevant files (images, videos, etc.)
- [ ] Stores document list with metadata in shared store
- [ ] Handles authentication and access errors gracefully
- [ ] Provides progress updates for large scans

## Technical Details
- Extends base Node class with prep/exec/post pattern
- Uses document scanning utilities from task-36
- Stores results in shared["document_sources"]
- Configuration in shared["scan_config"] includes:
  - Google Drive folder IDs
  - Local directory paths
  - File type filters
  - Date range filters

## Dependencies
- Document scanning utilities (task-36)
- Base Node class implementation

## Testing Requirements
- Test with various configuration options
- Test with mixed Google Drive and local sources
- Test error handling for inaccessible locations
- Test with large number of files
- Verify output structure matches schema