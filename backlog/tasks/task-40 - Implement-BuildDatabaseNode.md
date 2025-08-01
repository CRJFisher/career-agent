# Task: Implement BuildDatabaseNode

## Description
Implement the BuildDatabaseNode that structures extracted work experiences into the enhanced career database format, handling deduplication and validation.

## Acceptance Criteria
- [ ] Structures raw extractions into career database schema
- [ ] Deduplicates overlapping experiences from multiple documents
- [ ] Validates all required fields are present
- [ ] Merges information from multiple sources intelligently
- [ ] Handles conflicts in dates or details
- [ ] Generates the final career database YAML file
- [ ] Creates summary report of what was extracted

## Technical Details
- Extends base Node class
- Uses career database parser for validation
- Implements deduplication logic:
  - Match by company + role + approximate dates
  - Merge achievements and projects
  - Prefer more detailed/recent information
- Handles the enhanced schema with nested projects
- Saves output to career_database.yaml
- Stores in shared["career_database"]

## Dependencies
- Career database parser utility
- Enhanced career database schema
- ExtractExperienceNode output

## Testing Requirements
- Test with overlapping experiences
- Test conflict resolution
- Test schema validation
- Test with incomplete data
- Test output file generation
- Verify deduplication logic