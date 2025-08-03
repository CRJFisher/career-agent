---
id: task-48
title: Implement parallel LLM calls
status: Done
assignee: []
created_date: '2025-08-03'
updated_date: '2025-08-03'
labels: [performance, enhancement]
dependencies: []
---

## Description

While the system uses BatchNode for parallel document processing, the actual LLM calls within batch operations are still sequential. Implementing true parallel LLM calls would significantly improve performance, especially for ExtractExperienceNode which processes multiple documents.

## Acceptance Criteria

- [x] Modify LLMWrapper to support async/parallel calls
- [x] Implement connection pooling for API requests
- [x] Add rate limiting to respect API limits
- [x] Update BatchNode to leverage parallel LLM calls
- [x] Maintain error handling and retry logic
- [x] Add configuration for max parallel requests
- [x] Create performance benchmarks
- [x] Update affected nodes to use parallel calls where beneficial

## Implementation Plan

1. Research async libraries (asyncio, aiohttp)
2. Create AsyncLLMWrapper class
3. Implement connection pooling
4. Add rate limiting with backoff
5. Update BatchNode to use async execution
6. Modify ExtractExperienceNode for parallel processing
7. Add configuration options
8. Create performance tests
9. Document usage patterns

## Notes

Potential improvements:

- ExtractExperienceNode: Process multiple documents in parallel
- CompanyResearchAgent: Multiple search queries in parallel
- GenerationFlow: Generate CV and cover letter simultaneously

Challenges:

- API rate limits must be respected
- Error handling becomes more complex
- Need to maintain backwards compatibility


## Implementation Notes

### What Was Implemented

1. **AsyncLLMWrapper** (`utils/async_llm_wrapper.py`):
   - Complete async implementation using aiohttp
   - Connection pooling with session reuse
   - Token bucket rate limiting (configurable rate/period)
   - Concurrent request limiting with semaphores
   - Batch processing support with `call_llm_batch()`
   - Full compatibility with caching system

2. **Rate Limiting**:
   - Token bucket algorithm for smooth rate limiting
   - Configurable rate and period
   - Automatic request throttling
   - No external dependencies

3. **Async Nodes** (`async_nodes.py`):
   - **AsyncExtractExperienceNode**: Parallel document processing
   - **AsyncGenerationFlow**: Concurrent CV/cover letter generation
   - Uses PocketFlow's AsyncParallelBatchNode
   - Maintains all retry and error handling logic

4. **Performance Improvements**:
   - **5x speedup** for 10 documents (5s → 1s)
   - Scales with document count
   - Configurable concurrency limits
   - Minimal memory overhead

5. **Integration Features**:
   - Works with existing caching system
   - Environment-based configuration
   - Backward compatible API
   - Comprehensive error handling

6. **Testing & Documentation**:
   - 16 unit tests for async functionality
   - Performance benchmark script
   - Complete documentation in `docs/parallel_llm_processing.md`
   - Usage examples and troubleshooting

### Configuration

```bash
# Example configuration
export MAX_CONCURRENT_LLM=5    # Max parallel calls
export LLM_RATE_LIMIT=10       # Requests per second
export ASYNC_LLM_TIMEOUT=60    # Request timeout
```

### Performance Results

Benchmark results (10 documents, 0.5s simulated latency):
- Sequential: 5.03 seconds
- Parallel (5 concurrent): 1.01 seconds
- **Speedup: 5.0x faster**
- **Time saved: 80%**

### Usage Example

```python
# Using async node
from async_nodes import AsyncExtractExperienceNode

async def process_documents(shared_store):
    node = AsyncExtractExperienceNode(max_concurrent=5)
    await node.run_async(shared_store)
    return shared_store['extracted_experiences']
```
