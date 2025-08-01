# Task: Implement ExtractExperienceNode

## Description
Implement the ExtractExperienceNode that processes discovered documents and extracts work experience information using LLM-powered analysis.

## Acceptance Criteria
- [ ] Node processes document list from ScanDocumentsNode
- [ ] Uses document parsing utilities to extract text
- [ ] Employs LLM to identify and extract work experience
- [ ] Handles different document formats (resumes, project docs, etc.)
- [ ] Extracts all fields from enhanced career database schema
- [ ] Identifies nested projects within work experiences
- [ ] Batches LLM calls for efficiency

## Technical Details
- Extends base Node class or BatchNode for parallel processing
- Uses document parsing utilities from task-37
- Uses LLM wrapper for experience extraction
- Implements smart prompting to extract:
  - Job titles, companies, dates
  - Responsibilities and achievements
  - Projects with full details
  - Technologies and skills
  - Cultural fit information
- Stores raw extractions in shared["extracted_experiences"]

## Dependencies
- Document parsing utilities (task-37)
- LLM wrapper
- Enhanced career database schema

## Testing Requirements
- Test with various document types
- Test extraction accuracy with known documents
- Test handling of non-work documents
- Test batching and error recovery
- Verify all schema fields are extracted