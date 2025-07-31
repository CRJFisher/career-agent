---
id: task-30
title: Implement main orchestrator
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Create the main.py file that orchestrates all flows in sequence, manages the shared store, and handles input/output operations. This is the master orchestrator that chains together all phases: loading career database, extracting requirements, analyzing fit, researching company, assessing suitability, developing narrative, and generating materials. The main.py follows the pattern shown in the document with proper shared store initialization containing all required keys.
## Acceptance Criteria

- [ ] main.py created with proper entry point and imports
- [ ] Shared store initialized with all required keys from data contract
- [ ] Career database loaded using utils/database_parser
- [ ] Job specification text loaded from file or input
- [ ] All flows instantiated in correct order
- [ ] Sequential execution of flows implemented
- [ ] Each flow's output feeds next flow via shared store
- [ ] Final CV and cover letter extracted and saved to files
- [ ] Unit tests for orchestrator initialization and setup
- [ ] Integration tests for complete end-to-end pipeline execution
- [ ] Tests verify proper shared store management across flows
- [ ] Tests validate sequential flow execution and data passing
- [ ] Tests ensure career database and job spec loading works correctly
- [ ] Error handling tests for flow failures and recovery
- [ ] Tests verify final file output generation and formatting
- [ ] Performance tests for complete pipeline execution time

## Implementation Plan

1. Create main.py with if __name__ == '__main__' block\n2. Import all flows and utilities\n3. Initialize shared store dictionary with all keys\n4. Load career database using parser utility\n5. Load job specification text\n6. Instantiate all flows in sequence\n7. Execute flows passing shared store\n8. Export final materials to files
