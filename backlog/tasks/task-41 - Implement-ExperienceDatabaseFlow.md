# Task: Implement ExperienceDatabaseFlow

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