# Architecture Decisions Log

## Decision 001: PocketFlow Framework Implementation

**Date**: 2025-07-31  
**Status**: Implemented  
**Decision**: Implement PocketFlow framework directly in the project rather than installing as a dependency

### Context

- The-Pocket/PocketFlow is a minimalist 100-line framework
- Multiple repositories with similar names exist (Tencent/PocketFlow, Saoge123/PocketFlow)
- Framework philosophy emphasizes simplicity and avoiding vendor lock-in

### Decision

Embed the framework patterns directly in our codebase:

- `nodes.py`: Node base class and implementations
- `flow.py`: Flow orchestration and graph execution
- Shared store pattern throughout

### Consequences

- ✅ Full control over framework behavior
- ✅ No external dependency management
- ✅ Can customize for our specific needs
- ❌ Must maintain framework code ourselves
- ❌ No automatic updates from upstream

### Alternatives Considered

1. Install from GitHub repository
2. Create a separate package
3. Use a different orchestration framework (LangChain, etc.)

---

## Decision 002: YAML for Data Persistence

**Date**: 2025-07-31  
**Status**: Implemented  
**Decision**: Use YAML as the primary format for career databases and structured data

### Context

- Need human-readable format for career information
- Users should be able to edit their career data easily
- Complex nested structures required

### Decision

- YAML for all configuration and data files
- JSON Schema for validation
- Support both single files and directory structures

### Consequences

- ✅ Human-readable and editable
- ✅ Good support for complex structures
- ✅ Comments allowed for documentation
- ❌ Parsing overhead compared to JSON
- ❌ Indentation sensitivity can cause errors

### Alternatives Considered

1. JSON - Less readable, no comments
2. TOML - Less support for deep nesting
3. Database (SQLite) - Overkill for this use case

---

## Decision 003: Multi-Provider LLM Support

**Date**: 2025-07-31  
**Status**: Implemented  
**Decision**: Abstract LLM calls behind a provider-agnostic interface

### Context

- Different LLMs have different strengths
- API costs and availability vary
- Users may have preferences or existing API keys

### Decision

Created `LLMWrapper` with:

- Provider abstraction (OpenAI, Anthropic)
- Unified interface for all nodes
- Environment-based configuration
- Automatic retry logic

### Consequences

- ✅ Flexibility in LLM choice
- ✅ Easy to add new providers
- ✅ Cost optimization possible
- ❌ Additional abstraction layer
- ❌ Must handle provider-specific quirks

### Alternatives Considered

1. Hard-code to single provider
2. Use LangChain abstractions
3. Let each node handle its own LLM calls

---

## Decision 004: Structured Output via Prompting

**Date**: 2025-07-31  
**Status**: Implemented  
**Decision**: Use prompt engineering rather than function calling for structured output

### Context

- Need reliable YAML/JSON output from LLMs
- Function calling not universally supported
- Output consistency is critical

### Decision

- Detailed prompts with explicit format instructions
- One-shot examples in prompts
- Low temperature (0.3) for consistency
- Retry logic with parsing validation

### Consequences

- ✅ Works with any LLM
- ✅ Full control over output format
- ✅ Can iterate on prompts easily
- ❌ More tokens used in prompts
- ❌ Occasional parsing failures require retries

### Alternatives Considered

1. OpenAI function calling
2. JSON mode (limited availability)
3. Grammar-constrained generation

---

## Decision 005: Async-First Architecture

**Date**: 2025-07-31  
**Status**: Implemented  
**Decision**: Use async/await throughout the codebase

### Context

- LLM calls are I/O bound
- Future flows may parallelize operations
- Modern Python best practices

### Decision

- All nodes use async execute methods
- Flows orchestrate with asyncio
- Async utilities for file I/O planned

### Consequences

- ✅ Better resource utilization
- ✅ Future parallelization possible
- ✅ Modern Python patterns
- ❌ Slightly more complex testing
- ❌ Requires Python 3.7+

### Alternatives Considered

1. Synchronous with threading
2. Multiprocessing for CPU-bound work
3. Mixed sync/async approach

---

## Decision 006: Schema Validation Strategy

**Date**: 2025-07-31  
**Status**: Implemented  
**Decision**: Dual validation with code checks and JSON Schema

### Context

- Need to ensure data quality
- Want helpful error messages
- Schema documentation important

### Decision

- Markdown documentation for humans
- JSON Schema for programmatic validation
- Custom validation methods for business logic
- Graceful handling of validation errors

### Consequences

- ✅ Comprehensive validation
- ✅ Good documentation
- ✅ Machine-readable schemas
- ❌ Dual maintenance burden
- ❌ More complex validation flow

### Alternatives Considered

1. Pydantic models only
2. JSON Schema only
3. Custom validation framework

---

## Future Decisions to Make

1. **Caching Strategy**: How to cache LLM responses and parsed data
2. **State Persistence**: How to save/resume flow execution
3. **Concurrent Execution**: How many nodes can run in parallel
4. **Output Formats**: Support for different CV/cover letter formats
5. **Web Interface**: Whether to add a web UI later
