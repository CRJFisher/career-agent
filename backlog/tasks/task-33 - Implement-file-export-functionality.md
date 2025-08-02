---
id: task-33
title: Implement file export functionality
status: Complete
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create functionality to export generated CV and cover letter from shared store to markdown and text files. This is the final step in main.py that takes the generated content and writes it to the filesystem. The CV is saved as a .md file preserving Markdown formatting, while the cover letter is saved as a .txt file. File names should include timestamp or job details for organization.

## Acceptance Criteria

- [ ] Export function implemented in main.py
- [ ] CV content from shared['cv_markdown'] saved to .md file
- [ ] Cover letter from shared['cover_letter_text'] saved to .txt file
- [ ] Output directory created if not exists
- [ ] Filenames include timestamp for uniqueness
- [ ] Success messages displayed to user
- [ ] Error handling for write failures
- [ ] Optional PDF conversion mentioned in docs
- [ ] Unit tests for file export functionality
- [ ] Tests verify proper file creation with correct extensions
- [ ] Tests validate filename generation with timestamps
- [ ] Tests ensure output directory creation works correctly
- [ ] Tests verify content integrity in exported files
- [ ] Error handling tests for write permission issues
- [ ] Tests validate success message generation

## Implementation Plan

1. Create export_materials() function in main.py
2. Read cv_markdown from shared store
3. Read cover_letter_text from shared store
4. Create output directory if needed
5. Generate filenames with timestamp
6. Write CV to .md file
7. Write cover letter to .txt file
8. Display success messages with paths

## Implementation Details

**Note**: This functionality was implemented as part of task-30 (main orchestrator) as the `export_final_materials()` function.

### Implementation in main.py

1. **export_final_materials() function**:
   - Creates `outputs` directory using Path.mkdir(exist_ok=True)
   - Generates timestamp using datetime.now().strftime("%Y%m%d_%H%M%S")
   - Sanitizes job_title and company_name (replaces spaces with _, / with -)
   - Exports CV if cv_markdown exists in shared store
   - Exports cover letter if cover_letter_text exists
   - Handles missing content gracefully

2. **Filename Generation**:
   - Format: `{timestamp}_{company}_{job_title}_CV.md`
   - Format: `{timestamp}_{company}_{job_title}_CoverLetter.txt`
   - Example: `20240115_143022_TechCorp_Software-Engineer_CV.md`
   - Ensures unique filenames with timestamp prefix

3. **Optional PDF/DOCX Conversion**:
   - Attempts PDF generation for CV using pandoc with xelatex engine
   - Attempts DOCX generation for cover letter using pandoc
   - Gracefully handles when pandoc is not installed
   - Logs informational message when PDF generation skipped

4. **Success Logging**:
   - Uses checkmark (✓) for successful file writes
   - Uses info icon (ℹ) for skipped optional conversions
   - Logs each filename after successful write
   - Clear visual feedback for user

5. **Error Handling**:
   - Path operations use pathlib for cross-platform compatibility
   - Subprocess calls wrapped in try/except blocks
   - FileNotFoundError caught for missing pandoc
   - CalledProcessError caught for pandoc failures

### Test Coverage

In **tests/test_main_orchestrator.py**:

1. **test_export_cv_and_cover_letter**:
   - Mocks Path.mkdir, Path.write_text, subprocess.run
   - Verifies output directory creation
   - Confirms both files are written
   - Validates content passed to write_text

2. **test_handles_missing_content_gracefully**:
   - Tests with empty shared store
   - Ensures no exceptions raised
   - Verifies directory still created

3. **test_filename_sanitization**:
   - Tests special characters in job_title and company_name
   - Verifies slashes and special chars are replaced
   - Ensures valid filenames generated

### Integration with Pipeline

- Called as Step 7 in process_job_application()
- Also called at end of resume_workflow()
- Integrated into the complete pipeline flow
- Provides final user-facing output

### Key Features

1. **Timestamp-based naming**: Prevents filename collisions
2. **Sanitization**: Handles special characters in job titles
3. **Optional conversions**: PDF/DOCX when pandoc available
4. **Graceful degradation**: Works without pandoc
5. **Clear feedback**: Visual success indicators
