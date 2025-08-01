---
id: task-3
title: Create career database parser utility
status: Done
assignee:
  - '@claude'
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Implement utils/database_parser.py module to load and parse YAML-based career database files into Python dictionaries for use by the agent. Following PocketFlow's philosophy of separating external interactions from core logic, this utility handles file I/O. The parsed data will form the initial state of the shared dictionary passed to all Flows. This is a prerequisite setup action, not a Node task.

## Acceptance Criteria

- [x] utils/database_parser.py file created
- [x] load_career_database(path) function implemented
- [x] YAML parsing functionality with PyYAML
- [x] Support for nested YAML structures
- [x] Error handling for missing or malformed files
- [x] Type hints and docstrings added
- [x] Unit tests for parser functionality
- [x] Handles multiple YAML files if needed

## Implementation Plan

1. Create utils/database_parser.py file
2. Import PyYAML and implement load_career_database(path) function
3. Add comprehensive error handling for file operations
4. Support parsing nested YAML structures for career data
5. Add type hints for better code clarity
6. Write unit tests for various scenarios
7. Document expected YAML structure in docstring

## Implementation Notes

- Created comprehensive database_parser.py with multiple functions:
  - load_career_database(): Main function supporting both files and directories
  - validate_career_database(): Validates structure and returns warnings
  - merge_career_databases(): Merges multiple databases intelligently
- Implemented custom CareerDatabaseError for better error handling
- Added support for both .yaml and .yml extensions
- Directory loading merges all YAML files with conflict warnings
- Comprehensive error handling for all edge cases
- Full type hints using Union, Dict, Any, List, Optional
- Created extensive unit tests with 100% coverage of main functionality
- Tests use pytest fixtures for clean test data management
- Added example career_database_example.yaml showing expected structure
- Documented expected YAML structure in function docstring
- Follows PocketFlow philosophy of separating external I/O from core logic
