---
id: task-3
title: Create career database parser utility
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Implement utils/database_parser.py module to load and parse YAML-based career database files into Python dictionaries for use by the agent. Following PocketFlow's philosophy of separating external interactions from core logic, this utility handles file I/O. The parsed data will form the initial state of the shared dictionary passed to all Flows. This is a prerequisite setup action, not a Node task.
## Acceptance Criteria

- [ ] utils/database_parser.py file created
- [ ] load_career_database(path) function implemented
- [ ] YAML parsing functionality with PyYAML
- [ ] Support for nested YAML structures
- [ ] Error handling for missing or malformed files
- [ ] Type hints and docstrings added
- [ ] Unit tests for parser functionality
- [ ] Handles multiple YAML files if needed

## Implementation Plan

1. Create utils/database_parser.py file\n2. Import PyYAML and implement load_career_database(path) function\n3. Add comprehensive error handling for file operations\n4. Support parsing nested YAML structures for career data\n5. Add type hints for better code clarity\n6. Write unit tests for various scenarios\n7. Document expected YAML structure in docstring
