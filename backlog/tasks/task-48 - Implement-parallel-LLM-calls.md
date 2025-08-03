---
id: task-48
title: Implement parallel LLM calls
status: Todo
assignee: []
created_date: '2025-08-03'
updated_date: '2025-08-03'
labels: [performance, enhancement]
dependencies: []
---

## Description

While the system uses BatchNode for parallel document processing, the actual LLM calls within batch operations are still sequential. Implementing true parallel LLM calls would significantly improve performance, especially for ExtractExperienceNode which processes multiple documents.

## Acceptance Criteria

- [ ] Modify LLMWrapper to support async/parallel calls
- [ ] Implement connection pooling for API requests
- [ ] Add rate limiting to respect API limits
- [ ] Update BatchNode to leverage parallel LLM calls
- [ ] Maintain error handling and retry logic
- [ ] Add configuration for max parallel requests
- [ ] Create performance benchmarks
- [ ] Update affected nodes to use parallel calls where beneficial

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