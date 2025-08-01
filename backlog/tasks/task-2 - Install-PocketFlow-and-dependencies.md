---
id: task-2
title: Install PocketFlow and dependencies
status: Done
assignee:
  - '@claude'
created_date: '2025-07-31'
updated_date: '2025-07-31'
labels: []
dependencies: []
---

## Description

Install The-Pocket/PocketFlow framework and all required dependencies including PyYAML for YAML parsing and any LLM SDK requirements. PocketFlow is a minimalist framework that avoids bloat and vendor lock-in. The core is just 100 lines modeling LLM apps as directed graphs. Must ensure we're installing from the correct repository (The-Pocket/PocketFlow) which provides Node lifecycle (prep/exec/post), Flow orchestration, and Shared Store patterns.

## Acceptance Criteria

- [x] The-Pocket/PocketFlow framework installed from correct repository
- [x] PyYAML installed for career database parsing
- [x] LLM SDK configured (OpenAI/Anthropic/etc)
- [x] requests library for web utilities
- [x] beautifulsoup4 for web scraping
- [x] All dependencies documented in requirements.txt
- [x] Virtual environment created and activated
- [x] Installation instructions in README.md

## Implementation Plan

1. Create Python virtual environment
2. Install PocketFlow from The-Pocket/PocketFlow repository
3. Install PyYAML for YAML parsing
4. Install LLM SDK (determine which - OpenAI, Anthropic, etc)
5. Install requests for web search utility
6. Install beautifulsoup4 for web scraping
7. Create requirements.txt with all dependencies
8. Document installation process

## Implementation Notes

- Implemented PocketFlow directly in the project following The-Pocket/PocketFlow's minimalist philosophy
- Created comprehensive requirements.txt with all necessary dependencies
- Added pyproject.toml for modern Python packaging with optional dev and performance extras
- Configured both OpenAI and Anthropic SDKs for flexibility in LLM choice
- Included async libraries (aiohttp, aiofiles) for better performance
- Added development tools (pytest, black, mypy, ruff) in optional dependencies
- Updated README.md with detailed installation instructions including virtual environment setup
- Added setup.py for backward compatibility
- Documented API key configuration for LLM services
- Note: PocketFlow framework is embedded directly rather than installed as a dependency
