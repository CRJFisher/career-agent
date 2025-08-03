---
id: task-44
title: Remove duplicate placeholder nodes
status: Todo
assignee: []
created_date: '2025-08-03'
updated_date: '2025-08-03'
labels: [cleanup, technical-debt]
dependencies: []
---

## Description

The codebase contains duplicate node implementations - old placeholder nodes (lines 583-651 in nodes.py) that were later replaced with full implementations (lines 3133+). These placeholders have TODO comments and should be removed to avoid confusion.

## Acceptance Criteria

- [ ] Remove placeholder ScanDocumentsNode class (around line 583)
- [ ] Remove placeholder ExtractExperienceNode class (around line 623)
- [ ] Ensure no references to the old placeholder implementations exist
- [ ] Verify all tests still pass after removal
- [ ] Update any imports if necessary

## Implementation Plan

1. Identify exact line ranges of placeholder implementations
2. Remove the placeholder classes
3. Run all tests to ensure nothing breaks
4. Check for any stray references to the old implementations