---
id: task-38
title: Implement ScanDocumentsNode
status: completed
assignee:
  - unassigned
created_date: ''
updated_date: '2025-08-02'
labels: []
dependencies:
  - task-36
priority: high
---

## Description

Implement the ScanDocumentsNode that discovers and lists all relevant documents from configured Google Drive folders and local directories for work experience extraction.

## Acceptance Criteria

- [x] Node reads configuration for source locations from shared store
- [x] Scans Google Drive folders using document scanning utility
- [x] Scans local directories for relevant files
- [x] Filters out non-relevant files (images, videos, etc.)
- [x] Stores document list with metadata in shared store
- [x] Handles authentication and access errors gracefully
- [x] Provides progress updates for large scans

## Technical Details

- Extends base Node class with prep/exec/post pattern
- Uses document scanning utilities from task-36
- Stores results in shared["document_sources"]
- Configuration in shared["scan_config"] includes:
  - Google Drive folder IDs
  - Local directory paths
  - File type filters
  - Date range filters

## Implementation Plan

### Node Structure

```python
class ScanDocumentsNode(Node):
    """Scans configured sources for work experience documents."""
    
    def prep(self, shared: dict) -> dict:
        """Read scan configuration from shared store."""
        return {
            "google_drive_folders": shared.get("scan_config", {}).get("google_drive_folders", []),
            "local_directories": shared.get("scan_config", {}).get("local_directories", []),
            "file_types": shared.get("scan_config", {}).get("file_types", [".pdf", ".docx", ".md"]),
            "date_filter": shared.get("scan_config", {}).get("date_filter", {})
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Execute document scanning across all configured sources."""
        # Use scan_documents() from document_scanner.py
        # Aggregate results from all sources
        # Handle errors gracefully
        return {"documents": [...]}
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Store discovered documents in shared store."""
        shared["document_sources"] = exec_res["documents"]
        return "continue"
```

### Configuration Schema

```yaml
scan_config:
  google_drive_folders:
    - folder_id: "1234567890"
      name: "Work Projects"
    - folder_id: "0987654321"
      name: "Career Documents"
  local_directories:
    - path: "~/Documents/Career"
    - path: "~/Projects/Portfolio"
  file_types: [".pdf", ".docx", ".md", ".txt"]
  date_filter:
    min_date: "2020-01-01"
    max_date: null  # Current date
```

### Output Schema

```yaml
document_sources:
  - path: "path/to/document"
    name: "Resume_2024.pdf"
    type: ".pdf"
    size: 125000
    modified_date: "2024-01-15T10:30:00"
    source: "local"
    additional_data:
      relative_path: "Career/Resume_2024.pdf"
  - path: "gdrive_file_id"
    name: "Project_Summary.docx"
    type: ".docx"
    size: 45000
    modified_date: "2024-02-20T14:45:00"
    source: "google_drive"
    additional_data:
      folder_id: "1234567890"
      web_view_link: "https://drive.google.com/..."
```

## Dependencies

- Document scanning utilities (task-36)
- Base Node class implementation

## Testing Requirements

- Test with various configuration options
- Test with mixed Google Drive and local sources
- Test error handling for inaccessible locations
- Test with large number of files
- Verify output structure matches schema

## Error Handling

1. **Authentication Failures**
   - Log error but continue with other sources
   - Add error details to shared["scan_errors"]

2. **Access Denied**
   - Skip inaccessible directories/folders
   - Record in error log

3. **Invalid Configuration**
   - Validate config before scanning
   - Provide clear error messages

## Performance Considerations

- Implement progress callbacks for UI updates
- Consider parallel scanning for multiple sources
- Cache results if re-scanning same sources
- Limit result size to prevent memory issues

## Integration Notes

- First node in ExperienceDatabaseFlow
- Provides input for ExtractExperienceNode
- Must handle empty results gracefully
- Should deduplicate files found in multiple locations

## Implementation Details

### Completed on 2025-08-02

1. **Implemented ScanDocumentsNode** in `nodes.py:2647-2753`
   - Follows the standard prep/exec/post pattern
   - Reads configuration from shared["scan_config"]
   - Supports both Google Drive and local directory scanning
   - Handles date filtering and file type filtering
   - Stores results in shared["document_sources"]

2. **Error Handling**
   - Gracefully handles scan failures for individual paths
   - Continues scanning other sources if one fails
   - Stores errors in shared["scan_errors"] for visibility
   - Logs warnings for inaccessible files/directories

3. **Key Features**
   - Automatic home directory expansion for paths like "~/Documents"
   - Support for mixed Google Drive and local sources
   - Deduplication handled by document_scanner utility
   - Progress logging with total documents found

4. **Testing**
   - Created comprehensive unit tests in `tests/test_scan_documents_node.py`
   - Tests cover all acceptance criteria
   - 11 test cases all passing
   - Includes edge cases like scan errors and mixed sources
