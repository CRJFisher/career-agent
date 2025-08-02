---
id: task-30
title: Implement main orchestrator
status: Complete
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-02'
labels: []
dependencies: []
---

## Description

Create the main.py file that orchestrates all flows in sequence, manages the shared store, and handles input/output operations. This is the master orchestrator that chains together all phases: loading career database, extracting requirements, analyzing fit, researching company, assessing suitability, developing narrative, and generating materials. The main.py follows the pattern shown in the document with proper shared store initialization containing all required keys.

## Acceptance Criteria

- [x] main.py created with proper entry point and imports
- [x] Shared store initialized with all required keys from data contract
- [x] Career database loaded using utils/database_parser
- [x] Job specification text loaded from file or input
- [x] All flows instantiated in correct order
- [x] Sequential execution of flows implemented
- [x] Each flow's output feeds next flow via shared store
- [x] Final CV and cover letter extracted and saved to files
- [x] Unit tests for orchestrator initialization and setup
- [x] Integration tests for complete end-to-end pipeline execution
- [x] Tests verify proper shared store management across flows
- [x] Tests validate sequential flow execution and data passing
- [x] Tests ensure career database and job spec loading works correctly
- [x] Error handling tests for flow failures and recovery
- [x] Tests verify final file output generation and formatting
- [x] Performance tests for complete pipeline execution time

## Implementation Plan

1. Create main.py with if __name__ == '__main__' block
2. Import all flows and utilities
3. Initialize shared store dictionary with all keys
4. Load career database using parser utility
5. Load job specification text
6. Instantiate all flows in sequence
7. Execute flows passing shared store
8. Export final materials to files

## Implementation Details

### Main Orchestrator Enhancements

1. __Updated main.py__ with complete pipeline orchestration:
   - Refactored imports to include all 7 flows
   - Added CompanyResearchAgent and AssessmentFlow
   - Improved documentation and structure

2. __initialize_shared_store() function__:
   - Implements complete data contract with all required keys
   - Initializes all flow outputs as None
   - Sets configuration flags (enable_company_research, etc.)
   - Includes current_date for document generation
   - Validates against shared store data contract

3. __process_job_application() function__ - Complete 7-step pipeline:
   - Step 1: Extract requirements (RequirementExtractionFlow)
   - Step 2: Analyze fit (AnalysisFlow) with checkpoint support
   - Step 3: Company research (CompanyResearchAgent) - optional
   - Step 4: Suitability assessment (AssessmentFlow)
   - Step 5: Develop narrative (NarrativeFlow) with checkpoint
   - Step 6: Generate documents (GenerationFlow)
   - Step 7: Export final materials
   - Progress logging with clear step indicators
   - Error handling for failed flows
   - Returns complete shared store for testing

4. __export_final_materials() function__:
   - Creates outputs directory with timestamp
   - Sanitizes filenames (handles special characters)
   - Exports CV as .md file
   - Exports cover letter as .txt file
   - Optional PDF generation via pandoc
   - Optional DOCX generation for cover letter
   - Success logging with checkmarks

5. __resume_workflow() function__:
   - Loads checkpoint data from YAML file
   - Supports resuming from "analysis" or "narrative" checkpoints
   - Continues remaining flows based on checkpoint
   - Maintains shared store state across resume
   - Error handling for missing checkpoints

6. __Enhanced CLI interface__:
   - --job-file: Path to job description
   - --job-title: Position title (required)
   - --company: Company name (required)
   - --company-url: Optional company website
   - --career-db: Path to career database (default: career_database.yaml)
   - --skip-research: Skip company research phase
   - --resume: Resume from checkpoint (analysis/narrative)
   - --demo: Run with sample data
   - Helpful examples in epilog
   - Better error messages for missing arguments

7. __Demo mode implementation__:
   - Sample job description for ML Platform role
   - Sample career database with realistic data
   - Demonstrates full pipeline functionality
   - Useful for testing and development

### Test Coverage

1. __tests/test_main_orchestrator.py__:
   - TestInitializeSharedStore: Validates shared store structure
   - TestProcessJobApplication: Tests flow execution order
   - TestExportFinalMaterials: Tests file export functionality
   - TestResumeWorkflow: Tests checkpoint resume
   - TestLoadConfig: Tests configuration loading
   - Mock-based testing for isolation

2. __tests/test_integration_pipeline.py__:
   - TestEndToEndPipeline: Full pipeline with mocked LLM
   - TestErrorHandling: Graceful failure scenarios
   - TestPerformance: Timing constraints
   - Shared store data flow validation
   - Checkpoint pause/resume testing

### Key Improvements

1. __Complete Flow Integration__: All 7 flows properly orchestrated
2. __Checkpoint Support__: Pause/resume at analysis and narrative stages
3. __Company Research__: Optional AI-driven company research
4. __Better UX__: Clear progress indicators and helpful messages
5. __Error Resilience__: Graceful handling of failures
6. __Testing__: Comprehensive unit and integration tests
7. __Documentation__: Clear help text and examples
