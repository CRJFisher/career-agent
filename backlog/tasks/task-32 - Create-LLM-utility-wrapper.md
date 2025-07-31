---
id: task-32
title: Create LLM utility wrapper
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Implement a utility module for LLM interactions that handles API calls, error handling, and response parsing for all nodes. This centralizes LLM logic following PocketFlow's separation of concerns. The wrapper supports multiple providers (OpenAI, Anthropic, etc.), implements retry logic, handles rate limiting, and provides consistent interface for all nodes. This is critical infrastructure that all LLM-using nodes depend on.
## Acceptance Criteria

- [ ] utils/llm_wrapper.py created with provider abstraction
- [ ] Generic call_llm() function with prompt and parameters
- [ ] Support for multiple providers via configuration
- [ ] Retry logic with exponential backoff for failures
- [ ] Rate limiting and quota management implemented
- [ ] Response parsing and validation utilities
- [ ] Error handling for malformed responses
- [ ] Environment variable configuration for API keys

## Implementation Plan

1. Create utils/llm_wrapper.py module\n2. Design provider abstraction interface\n3. Implement call_llm() with standard parameters\n4. Add provider-specific implementations\n5. Implement retry logic and backoff\n6. Add rate limiting controls\n7. Create response parsing utilities\n8. Support environment configuration
