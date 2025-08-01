---
id: task-14
title: Create web scraper utility
status: Done
assignee: []
created_date: '2025-07-31'
updated_date: '2025-08-01'
labels: []
dependencies: []
---

## Description

Implement utils/web_scraper.py module that extracts clean readable text from URLs for company research purposes. This utility handles the complexity of parsing HTML, removing navigation/ads, and extracting main content. The agent uses this to read company About pages, blog posts, and news articles. Must handle various content types and website structures robustly.

## Acceptance Criteria

- [x] utils/web_scraper.py file created with scraping functionality
- [x] scrape_url(url: str) function returns clean text content
- [x] HTML parsing with BeautifulSoup implemented
- [x] Main content extraction removing nav/footer/ads
- [x] Error handling for unreachable URLs and timeouts
- [x] Support for common content types (HTML/PDF)
- [x] User-agent headers to avoid blocking
- [x] Text cleaning and normalization applied
- [x] Unit tests created for all public methods
- [x] Test coverage of at least 80%
- [x] Mock-based testing for external dependencies (HTTP requests, file systems)
- [x] Error cases tested (unreachable URLs, timeouts, malformed HTML, blocked requests)
- [x] Edge cases tested (empty pages, unsupported content types, large files)

## Implementation Plan

1. Create utils/web_scraper.py module
2. Implement scrape_url(url) function
3. Use BeautifulSoup for HTML parsing
4. Implement content extraction heuristics
5. Add timeout and error handling
6. Support different content types
7. Add proper user-agent headers
8. Implement text cleaning and formatting

## Completion Summary

**Completed on**: 2025-08-01

### Implementation Details

- Implemented WebScraper class with robust content extraction
- Smart content detection using multiple strategies:
  - Searches for semantic HTML tags (article, main)
  - Falls back to largest text block heuristic
  - Removes navigation, ads, sidebars automatically
- HTTP session with retry strategy and timeout handling
- Support for both HTML and PDF content types
- Text cleaning removes short lines and excessive whitespace
- Metadata extraction for titles and Open Graph data

### Key Features

1. **Intelligent Extraction**: Multiple strategies to find main content
2. **Clean Output**: Removes ads, navigation, scripts, styles
3. **PDF Support**: Extracts text from PDF documents using pypdf
4. **Error Resilience**: Retries, timeouts, and graceful degradation
5. **Anti-blocking**: User-agent rotation and proper headers
6. **Batch Processing**: Can scrape multiple URLs efficiently

### Test Coverage

- Created comprehensive test suite with 21 passing tests
- All HTTP operations properly mocked
- Tests cover HTML parsing, PDF extraction, error cases
- Integration test included but skipped by default

### Notes

- Uses pypdf instead of deprecated PyPDF2
- Content extraction heuristics work well for most sites
- Minimum text length threshold prevents extracting navigation items
- Convenience functions provided for simple usage
