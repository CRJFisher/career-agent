---
id: task-33
title: Implement file export functionality
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
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

## Implementation Plan

1. Create export_materials() function in main.py\n2. Read cv_markdown from shared store\n3. Read cover_letter_text from shared store\n4. Create output directory if needed\n5. Generate filenames with timestamp\n6. Write CV to .md file\n7. Write cover letter to .txt file\n8. Display success messages with paths
