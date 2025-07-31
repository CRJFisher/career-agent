---
id: task-13
title: Create web search utility
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Implement utils/web_search.py module that provides web search functionality for the company research agent. Following PocketFlow's philosophy of separating external interactions from core logic, this utility encapsulates web search API calls. The agent will use this to find relevant URLs about the company including official website, news articles, and blog posts. Must handle rate limiting and API failures gracefully.
## Acceptance Criteria

- [ ] utils/web_search.py file created with search function
- [ ] search(query: str) function returns list of results
- [ ] Each result contains URL title and snippet
- [ ] Configurable search engine backend (Google/Bing/DuckDuckGo)
- [ ] Error handling for API failures and rate limits
- [ ] Retry logic with exponential backoff implemented
- [ ] Results filtered for relevance and quality
- [ ] Environment variables for API keys supported

## Implementation Plan

1. Create utils/web_search.py module\n2. Implement search(query) function signature\n3. Add support for search engine API (determine which to use)\n4. Structure results as list of dicts with url, title, snippet\n5. Implement rate limiting and retry logic\n6. Add error handling for network issues\n7. Support configuration via environment variables\n8. Add logging for debugging purposes
