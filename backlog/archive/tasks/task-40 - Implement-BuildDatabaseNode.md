---
id: task-40
title: Implement BuildDatabaseNode
status: completed
assignee:
  - unassigned
created_date: ''
updated_date: '2025-08-03'
labels: []
dependencies:
  - task-39
priority: high
---

## Description

Implement the BuildDatabaseNode that structures extracted work experiences into the enhanced career database format, handling deduplication and validation.

## Acceptance Criteria

- [x] Structures raw extractions into career database schema
- [x] Deduplicates overlapping experiences from multiple documents
- [x] Validates all required fields are present
- [x] Merges information from multiple sources intelligently
- [x] Handles conflicts in dates or details
- [x] Generates the final career database YAML file
- [x] Creates summary report of what was extracted

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

## Implementation Plan

### Node Structure

```python
class BuildDatabaseNode(Node):
    """Builds structured career database from extracted experiences."""
    
    def prep(self, shared: dict) -> dict:
        """Prepare extracted experiences for processing."""
        return {
            "extracted_experiences": shared.get("extracted_experiences", []),
            "existing_database": shared.get("existing_career_database"),
            "output_path": shared.get("database_output_path", "career_database.yaml")
        }
    
    def exec(self, prep_res: dict) -> dict:
        """Build and deduplicate career database."""
        # 1. Aggregate all experiences
        all_experiences = self.aggregate_experiences(prep_res["extracted_experiences"])
        
        # 2. Deduplicate and merge
        merged_experiences = self.deduplicate_experiences(all_experiences)
        
        # 3. Structure into career database
        career_db = self.build_database(merged_experiences)
        
        # 4. Merge with existing if provided
        if prep_res["existing_database"]:
            career_db = self.merge_with_existing(career_db, prep_res["existing_database"])
        
        # 5. Validate against schema
        self.validate_database(career_db)
        
        # 6. Generate summary report
        summary = self.generate_summary(career_db, prep_res["extracted_experiences"])
        
        return {
            "career_database": career_db,
            "summary": summary
        }
    
    def post(self, shared: dict, prep_res: dict, exec_res: dict) -> str:
        """Save database and store in shared."""
        # Save to file
        save_career_database(exec_res["career_database"], prep_res["output_path"])
        
        # Store in shared
        shared["career_database"] = exec_res["career_database"]
        shared["build_summary"] = exec_res["summary"]
        
        return "complete"
```

### Deduplication Strategy

```python
def deduplicate_experiences(experiences: List[dict]) -> List[dict]:
    """Intelligent deduplication of work experiences."""
    
    # Group by company and overlapping dates
    grouped = {}
    for exp in experiences:
        key = (exp["company"].lower(), exp["title"].lower())
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(exp)
    
    # Merge overlapping experiences
    merged = []
    for key, group in grouped.items():
        if len(group) == 1:
            merged.append(group[0])
        else:
            # Merge logic
            merged_exp = merge_experience_group(group)
            merged.append(merged_exp)
    
    return merged

def merge_experience_group(group: List[dict]) -> dict:
    """Merge multiple sources of same experience."""
    # Use most complete as base
    base = max(group, key=lambda x: len(str(x)))
    
    # Merge additional details
    for exp in group:
        # Merge achievements (unique)
        base["achievements"].extend(
            a for a in exp.get("achievements", [])
            if a not in base["achievements"]
        )
        
        # Merge projects (by name)
        # ... similar logic
    
    return base
```

### Validation Rules

1. **Required Fields**
   - Every experience must have: company, title, start_date
   - Every project must have: name, role, description

2. **Date Consistency**
   - End dates after start dates
   - No future dates beyond reasonable range
   - Handle "present" or null end dates

3. **Data Quality**
   - Remove duplicate achievements
   - Standardize technology names
   - Fix common typos

### Summary Report Schema

```yaml
build_summary:
  total_documents_processed: 15
  experiences_extracted: 8
  experiences_after_dedup: 5
  date_range: "2015-01 to present"
  companies:
    - name: "Tech Corp"
      experiences: 2
      projects: 5
  technologies_found: ["Python", "JavaScript", "AWS", ...]
  extraction_quality:
    high_confidence: 12
    medium_confidence: 3
    low_confidence: 0
  issues:
    - "Missing end date for Tech Corp experience"
    - "Conflicting titles in two documents"
```

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

## Error Handling

1. **Validation Failures**
   - Log specific validation errors
   - Attempt to fix common issues
   - Provide clear error messages

2. **Merge Conflicts**
   - Use confidence scores to resolve
   - Prefer more recent/detailed source
   - Log conflicts for review

3. **Missing Required Fields**
   - Use sensible defaults where possible
   - Mark as incomplete in summary
   - Don't fail entire process

## Performance Considerations

- Efficient deduplication algorithms
- Batch validation operations
- Incremental updates for large databases

## Integration Notes

- Final node in experience extraction pipeline
- Output used by main application flow
- Can be run independently for updates
- Supports incremental building

## Implementation Details

### Completed on 2025-08-03

1. **Implemented BuildDatabaseNode** in `nodes.py:3158-3762`
   - Aggregates extracted experiences from multiple documents
   - Intelligent deduplication based on company/role normalization
   - Merges duplicate experiences and projects
   - Validates against career database JSON schema
   - Saves final database to YAML file

2. **Deduplication Features**
   - Normalizes company names (removes suffixes like Inc., LLC)
   - Normalizes job titles (Sr. → Senior, Software Engineer → Engineer)
   - Groups experiences by normalized company/title
   - Merges achievements, technologies, and projects
   - Prefers most specific/detailed information

3. **Merge Strategies**
   - **Smart merge**: Intelligently combines with existing database
   - **Replace**: Completely replaces existing database
   - **Append**: Simply adds new data to existing

4. **Data Standardization**
   - Technology name standardization (js → JavaScript, k8s → Kubernetes)
   - Date format standardization
   - Removes empty sections from final output
   - Cleans whitespace and formatting

5. **Summary Report**
   - Total documents processed
   - Extraction quality metrics (high/medium/low confidence)
   - Companies and project counts
   - All technologies found
   - Data completeness checks
   - Validation errors if any

6. **Error Handling**
   - Gracefully handles missing dates in experience sorting
   - Validates against schema and reports errors
   - Skips low-confidence extractions (< 0.3)

7. **Testing**
   - Created comprehensive unit tests in `tests/test_build_database_node.py`
   - 14 test cases covering all functionality
   - Tests deduplication, merging, standardization
   - All tests passing

8. **Integration**
   - Added save_career_database function to database_parser.py
   - Uses validate_with_schema for JSON schema validation
   - Outputs to configurable path (default: career_database.yaml)
