---
id: task-31
title: Implement shared store data contract
status: Complete
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Define and document the complete data contract for the shared store including all keys, data types, and flow dependencies. The shared store is the central nervous system enabling communication between all phases. This contract defines the API between components, ensuring modularity and debuggability. Document includes comprehensive table mapping each key to its producer and consumer flows, serving as the single source of truth for data dependencies.

## Acceptance Criteria

- [ ] Complete data contract documentation created
- [ ] Table with Key/Data Type/Produced By/Consumed By columns
- [ ] All 10 primary keys documented (career_db through cover_letter_text)
- [ ] Data types specified (dict/str/list) for each key
- [ ] Producer flow identified for each data element
- [ ] Consumer flows mapped showing dependencies
- [ ] Contract enforced through validation logic
- [ ] Documentation integrated into codebase
- [ ] Validation tests for data contract compliance
- [ ] Tests verify all documented keys are properly defined
- [ ] Tests validate data type consistency across flows
- [ ] Tests ensure producer-consumer relationships work correctly
- [ ] Contract validation helper function tests
- [ ] Tests verify shared store initialization includes all required keys

## Implementation Plan

1. Create data contract documentation file
2. Define table structure with four columns
3. Document career_db: dict from Initial Setup
4. Document job_spec_text through cover_letter_text
5. Map producer flows for each key
6. Map consumer flows showing usage
7. Add validation helper functions
8. Include contract in design documentation

## Implementation Details

### Files Created

1. **docs/shared_store_data_contract.md** - Comprehensive data contract:
   - Overview explaining shared store as central nervous system
   - Complete data contract table with 23 keys documented
   - Four columns: Key, Data Type, Produced By, Consumed By
   - Detailed data type definitions for complex structures
   - Flow dependencies section mapping producer → consumer relationships
   - Validation rules (required keys, type consistency, value constraints)
   - Usage examples

2. **utils/shared_store_validator.py** - Validation implementation:
   - SharedStoreValidator class with comprehensive validation
   - DATA_CONTRACT dict defining expected types for all keys
   - FLOW_REQUIREMENTS mapping flows to required inputs
   - Type validation with support for union types
   - Structure validation for complex types:
     - validate_requirements_structure()
     - validate_mapping_structure()
     - validate_gaps_structure()
     - validate_suitability_assessment()
     - validate_narrative_strategy()
   - validate_complete_store() for full validation
   - Helper functions: validate_shared_store(), log_validation_warnings()

3. **tests/test_shared_store_validator.py** - Comprehensive test suite:
   - TestSharedStoreValidator: Type and structure validation tests
   - TestValidationHelperFunctions: Helper function tests
   - TestDataContractCompliance: Contract matches implementation
   - Tests for all validation methods
   - Tests for error cases and edge conditions
   - Integration tests with main.py

### Data Contract Details

**Primary Keys Documented:**
- Initial setup keys: career_db, job_spec_text, job_title, company_name, etc.
- Flow output keys: requirements, requirement mappings, gaps, assessments, etc.
- System keys: checkpoint_data, configuration flags

**Key Features:**
- Every key has defined type (dict, str, list, int/float, bool, or None)
- Producer flow identified for each data element
- Consumer flows mapped showing data dependencies
- Complex structures fully defined (career_db, requirements, etc.)
- Validation rules for enums (strengths, severities)
- Score constraints (0-100 range)

### Design Documentation Updates

1. **docs/design.md** updated with:
   - Reference to shared store data contract document
   - Explanation of validation enforcement
   - Links to contract and validator in implementation notes

2. **utils/__init__.py** updated to export:
   - SharedStoreValidator
   - validate_shared_store
   - log_validation_warnings

### Key Design Decisions

1. **Central Contract**: Single source of truth for all data flow
2. **Type Safety**: Strict type checking with support for unions
3. **Flow Requirements**: Each flow declares required inputs
4. **Structure Validation**: Deep validation of complex data types
5. **Graceful Warnings**: Non-critical issues logged as warnings
6. **Testability**: Comprehensive test coverage of all validation

### Usage in Practice

The shared store validator is used to:
- Validate data before flows execute
- Ensure type consistency across flows
- Catch data contract violations early
- Provide helpful error messages
- Log warnings for potential issues

Example:
```python
# In a node's prep method
from utils import validate_shared_store

def prep(self, shared):
    validate_shared_store(shared, "CVGenerationNode")
    # Proceed knowing required fields exist and are correct type
```
