---
id: task-32
title: Create LLM utility wrapper
status: In Progress
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
- [ ] Unit tests for LLM wrapper functionality
- [ ] Tests verify provider abstraction works correctly
- [ ] Tests validate retry logic and exponential backoff
- [ ] Tests ensure rate limiting prevents API quota violations
- [ ] Mock API tests for response parsing and validation
- [ ] Error handling tests for various failure scenarios
- [ ] Integration tests with different LLM providers

## Implementation Plan

1. Create utils/llm_wrapper.py module\n2. Design provider abstraction interface\n3. Implement call_llm() with standard parameters\n4. Add provider-specific implementations\n5. Implement retry logic and backoff\n6. Add rate limiting controls\n7. Create response parsing utilities\n8. Support environment configuration

## Implementation Notes (Partial)

- Created utils/llm_wrapper.py with provider abstraction (as part of task-5)
- Implemented LLMProvider abstract base class
- Created OpenAIProvider and AnthropicProvider implementations
- Implemented LLMWrapper with unified interface
- Added call_llm() and call_llm_structured() methods
- Retry logic implemented using tenacity library
- Environment variable configuration supported
- Structured output parsing for YAML/JSON with retry logic
- Still needed: Rate limiting, quota management, comprehensive tests
