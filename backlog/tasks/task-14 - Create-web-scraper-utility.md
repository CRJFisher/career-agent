---
id: task-14
title: Create web scraper utility
status: To Do
assignee: []
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Implement utils/web_scraper.py module that extracts clean readable text from URLs for company research purposes. This utility handles the complexity of parsing HTML, removing navigation/ads, and extracting main content. The agent uses this to read company About pages, blog posts, and news articles. Must handle various content types and website structures robustly.
## Acceptance Criteria

- [ ] utils/web_scraper.py file created with scraping functionality
- [ ] scrape_url(url: str) function returns clean text content
- [ ] HTML parsing with BeautifulSoup implemented
- [ ] Main content extraction removing nav/footer/ads
- [ ] Error handling for unreachable URLs and timeouts
- [ ] Support for common content types (HTML/PDF)
- [ ] User-agent headers to avoid blocking
- [ ] Text cleaning and normalization applied

## Implementation Plan

1. Create utils/web_scraper.py module\n2. Implement scrape_url(url) function\n3. Use BeautifulSoup for HTML parsing\n4. Implement content extraction heuristics\n5. Add timeout and error handling\n6. Support different content types\n7. Add proper user-agent headers\n8. Implement text cleaning and formatting
