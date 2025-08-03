---
id: task-36
title: Create Document Scanning Utilities
status: completed
priority: high
assignee: assistant
created: 2024-01-01
updated: 2025-08-02
tags: [utilities, google-drive, file-scanning, experience-database]
dependencies: []
estimated_hours: 4
actual_hours: 3
---

## Description

Create utilities to scan and list documents from Google Drive folders and local directories. These utilities will be used by the ExperienceDatabaseFlow to discover work experience documents.

## Acceptance Criteria

- [x] Google Drive scanner can authenticate and list all documents in specified folders
- [x] Local file scanner can recursively find all .md, .pdf, .docx files in directories
- [x] Both scanners return standardized metadata (path, type, modified date, size)
- [x] Handle authentication errors gracefully
- [x] Support filtering by file type and date range
- [x] Create unit tests for both scanners

## Technical Details

- Use Google Drive API v3 for Google Drive access
- Support OAuth2 authentication flow
- Use pathlib for local file scanning
- Return results as list of dictionaries with consistent schema
- Implement in `utils/document_scanner.py`

## Implementation Details

### Core Components

1. **DocumentMetadata dataclass**
   - Standardized metadata structure for all documents
   - Fields: path, name, type, size, modified_date, source, additional_data
   - Includes `to_dict()` method for serialization

2. **DocumentScanner abstract base class**
   - Common interface for all scanner implementations
   - Built-in support for date filtering and file type filtering
   - Abstract `scan()` method for implementations

3. **LocalFileScanner**
   - Recursively scans local directories using pathlib
   - Handles permission errors gracefully
   - Returns files sorted by modification date (newest first)
   - Supports relative path tracking in additional_data

4. **GoogleDriveScanner**
   - OAuth2 authentication with token persistence
   - Maps Google MIME types to file extensions
   - Handles pagination for large folders
   - Includes web view links in additional_data
   - Graceful handling of authentication errors

5. **scan_documents() convenience function**
   - Auto-detects scanner type based on path
   - Combines results from multiple paths
   - Removes duplicates based on path
   - Unified interface for both scanner types

### Key Design Decisions

1. **Abstract Base Class Pattern**: Ensures consistent interface across scanner types
2. **Dataclass for Metadata**: Type-safe, immutable data structure
3. **OAuth2 Token Persistence**: Avoids re-authentication for every scan
4. **Graceful Error Handling**: Continue scanning even if some files are inaccessible
5. **Comprehensive Filtering**: Both date and file type filters at the scanner level

## Dependencies

- Google API Python Client (google-api-python-client>=2.100.0)
- OAuth2 libraries (google-auth-httplib2, google-auth-oauthlib)
- Local file system access (pathlib, os)

## Testing Requirements

- [x] Mock Google Drive API responses
- [x] Test with various file structures
- [x] Test error handling (no access, invalid paths)
- [x] Test filtering capabilities
- [x] 15 comprehensive unit tests covering all functionality

## Testing Summary

All tests pass successfully:

- DocumentMetadata creation and serialization
- LocalFileScanner directory scanning with filters
- GoogleDriveScanner with mocked API responses
- Error handling for invalid paths and authentication
- scan_documents() convenience function with auto-detection

## Files Created/Modified

- `/utils/document_scanner.py` - Main implementation (410 lines)
- `/tests/test_document_scanner.py` - Comprehensive tests (280 lines)
- `/requirements.txt` - Added Google API dependencies

## Notes

- Google Drive scanner requires OAuth2 credentials file (credentials.json)
- Token is persisted to token.pickle for subsequent runs
- Scanner supports common document formats: .md, .pdf, .docx, .doc, .txt
- Results are always sorted by modification date (newest first)

## Future Enhancements

- Add support for Google Docs export (currently just tracks them)
- Implement parallel scanning for multiple paths
- Add progress callbacks for large directories
- Support for additional cloud storage providers (Dropbox, OneDrive)
