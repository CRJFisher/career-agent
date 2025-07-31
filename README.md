# Career Application Agent

An intelligent job application customization system built with the PocketFlow framework.

## Framework Note

This project uses **The-Pocket/PocketFlow** - a minimalist 100-line LLM orchestration framework that models applications as directed graphs with Nodes, Flows, and a Shared Store.

**Important**: This is NOT the Tencent/PocketFlow or Saoge123/PocketFlow repositories. We specifically use The-Pocket's implementation for its simplicity and focus on LLM orchestration patterns.

## Overview

This agent automates the customization of job applications by:
1. Extracting requirements from job descriptions
2. Analyzing candidate fit based on their career database
3. Researching companies for additional context
4. Generating tailored CVs and cover letters

## Project Structure

```
career-agent/
├── nodes.py          # Node implementations (units of work)
├── flow.py           # Flow orchestration logic
├── main.py           # Main entry point and CLI
├── utils/            # External integrations (LLM, web, etc.)
├── docs/             # Documentation
│   └── design.md     # System design and architecture
└── backlog/          # Task management (via backlog.md)
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd career-agent

# Install dependencies (to be implemented)
pip install -r requirements.txt
```

## Usage

```bash
python main.py "job_description.txt" \
    --career-db career_history.yaml \
    --output-dir ./applications \
    --company-url https://example.com
```

## Development

This project uses backlog.md for task management. To view current tasks:

```bash
backlog task list --plain
```

## Architecture

The system is built as a directed graph of processing nodes:
- **Extraction**: Parse job descriptions into structured data
- **Analysis**: Evaluate candidate fit and identify gaps
- **Research**: Gather company-specific information
- **Assessment**: Score overall suitability
- **Narrative**: Develop application strategy
- **Generation**: Create customized documents

See `docs/design.md` for detailed architecture information.

## License

[License information to be added]