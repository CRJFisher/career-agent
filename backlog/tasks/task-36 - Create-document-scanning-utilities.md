# Task: Create Document Scanning Utilities

## Description
Create utilities to scan and list documents from Google Drive folders and local directories. These utilities will be used by the ExperienceDatabaseFlow to discover work experience documents.

## Acceptance Criteria
- [ ] Google Drive scanner can authenticate and list all documents in specified folders
- [ ] Local file scanner can recursively find all .md, .pdf, .docx files in directories
- [ ] Both scanners return standardized metadata (path, type, modified date, size)
- [ ] Handle authentication errors gracefully
- [ ] Support filtering by file type and date range
- [ ] Create unit tests for both scanners

## Technical Details
- Use Google Drive API v3 for Google Drive access
- Support OAuth2 authentication flow
- Use pathlib for local file scanning
- Return results as list of dictionaries with consistent schema
- Implement in `utils/document_scanner.py`

## Dependencies
- Google API Python Client
- OAuth2 libraries
- Local file system access

## Testing Requirements
- Mock Google Drive API responses
- Test with various file structures
- Test error handling (no access, invalid paths)
- Test filtering capabilities