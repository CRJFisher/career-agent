# Career Application Agent

An intelligent job application customization system built with the PocketFlow framework that automates the creation of tailored CVs and cover letters based on job requirements and candidate experience.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd career-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure LLM
export OPENROUTER_API_KEY="your-api-key-here"

# Build your career database from documents
python main.py build-database --source-dir ~/Documents/Career

# Generate application materials
python main.py apply --job-url "https://example.com/job-posting" --company "TechCorp"
```

## 📋 Overview

The Career Application Agent automates job application customization through:

1. **📄 Document Analysis**: Extracts your work experience from resumes, CVs, and other documents
2. **🎯 Requirements Extraction**: Parses job descriptions to understand what employers want
3. **🔍 Fit Analysis**: Maps your experience to job requirements, identifying strengths and gaps
4. **🏢 Company Research**: Gathers context about the company and role
5. **📝 Document Generation**: Creates tailored CVs and cover letters optimized for each position

### Key Features

- **🔄 Pause/Resume Workflow**: Review and edit analysis at key checkpoints
- **🤖 AI-Powered**: Uses LLMs for intelligent document processing and generation
- **📊 Structured Data**: YAML-based formats for easy editing and version control
- **🔧 Modular Design**: Easy to extend with new capabilities
- **✅ Validation**: Schema validation ensures data quality

## 🛠 Installation

### Prerequisites

- Python 3.8 or higher
- OpenRouter API key (for LLM access)
- Optional: Google Drive API credentials (for Google Docs access)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd career-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development (includes testing and linting tools)
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file with:

```bash
# Required
OPENROUTER_API_KEY=your-openrouter-api-key

# Optional
GOOGLE_DRIVE_CREDENTIALS_PATH=path/to/credentials.json
DEFAULT_LLM_MODEL=anthropic/claude-3-5-sonnet
```

## 📖 Usage Guide

### 1. Build Your Career Database

First, scan and extract your work experience from existing documents:

```bash
# Scan local documents
python main.py build-database \
  --source-dir ~/Documents/Career \
  --output career_database.yaml

# Include Google Drive documents
python main.py build-database \
  --source-dir ~/Documents/Career \
  --google-drive-folder "Career Documents" \
  --output career_database.yaml
```

### 2. Analyze a Job Opportunity

Extract and analyze job requirements:

```bash
# From a URL
python main.py analyze-job \
  --job-url "https://example.com/job-posting" \
  --career-db career_database.yaml

# From a file
python main.py analyze-job \
  --job-file job_description.txt \
  --career-db career_database.yaml
```

The system will:
1. Extract structured requirements
2. Map your experience to requirements
3. Identify strengths and gaps
4. **Pause for your review** (edit `outputs/analysis_output.yaml`)

### 3. Research the Company

Gather additional context:

```bash
python main.py research-company \
  --company "TechCorp" \
  --role "Senior Engineer"
```

### 4. Generate Application Materials

Create tailored CV and cover letter:

```bash
python main.py generate-materials \
  --analysis outputs/analysis_output.yaml \
  --narrative outputs/narrative_output.yaml \
  --output-dir applications/techcorp/
```

### 5. Complete Workflow

Or run the entire pipeline:

```bash
python main.py apply \
  --job-url "https://example.com/job-posting" \
  --company "TechCorp" \
  --career-db career_database.yaml \
  --output-dir applications/techcorp/
```

## 🏗 Architecture

### Framework: PocketFlow

This project uses **The-Pocket/PocketFlow** - a minimalist 100-line LLM orchestration framework that models applications as directed graphs.

**Important**: This is NOT the Tencent/PocketFlow or Saoge123/PocketFlow repositories. We use The-Pocket's implementation for its simplicity and focus on LLM orchestration.

### Core Concepts

1. **Nodes**: Discrete units of work (e.g., ExtractRequirementsNode)
2. **Flows**: Directed graphs of nodes (e.g., AnalysisFlow)
3. **Shared Store**: Central data repository for node communication

### Project Structure

```
career-agent/
├── main.py                 # CLI entry point
├── nodes.py               # All node implementations
├── flow.py                # Flow orchestrations
├── pocketflow.py          # Core framework (100 lines)
├── utils/                 # Utilities and integrations
│   ├── llm_wrapper.py     # LLM abstraction
│   ├── document_scanner.py # Document discovery
│   └── ...
├── docs/                  # Documentation
│   ├── design.md         # Architecture details
│   └── ...
├── tests/                # Test suite
└── outputs/              # Generated files
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_nodes.py
```

### Adding New Nodes

1. Create node class in `nodes.py`:
```python
class MyNewNode(Node):
    def prep(self, shared):
        # Read from shared store
        return {"data": shared.get("input_data")}
    
    def exec(self, prep_res):
        # Process data (often LLM calls)
        return {"result": process(prep_res["data"])}
    
    def post(self, shared, prep_res, exec_res):
        # Update shared store
        shared["output_data"] = exec_res["result"]
        return "continue"  # or next action
```

2. Add to appropriate flow in `flow.py`
3. Write tests in `tests/`

### Code Style

```bash
# Format code
black .

# Lint
flake8

# Type check
mypy .
```

## 🐛 Troubleshooting

### Common Issues

#### LLM API Errors
```bash
# Check your API key
echo $OPENROUTER_API_KEY

# Test connection
python -c "from utils.llm_wrapper import get_default_llm_wrapper; llm = get_default_llm_wrapper(); print(llm.test_connection())"
```

#### Document Parsing Issues
- Ensure documents are in supported formats: PDF, DOCX, MD, TXT
- Check file permissions
- For Google Drive, verify API credentials

#### Memory Issues with Large Documents
```bash
# Process in smaller batches
python main.py build-database --batch-size 5
```

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python main.py apply --job-url "..." --debug
```

## 📚 Documentation

- **[System Design](docs/design.md)**: Architecture and technical details
- **[API Reference](docs/api_reference.md)**: Node and flow documentation
- **[Data Schemas](docs/)**: Career database and requirements formats
- **[Developer Guide](docs/developer_guide.md)**: Contributing and extending

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on [The-Pocket/PocketFlow](https://github.com/The-Pocket/pocketflow) framework
- Powered by [OpenRouter](https://openrouter.ai) for LLM access
- Inspired by the need for better job application tools

## 📧 Contact

For questions or feedback:
- Open an issue on GitHub
- Email: [your-email@example.com]

---

**Note**: This tool is designed to assist with job applications but should not replace personal review and customization of application materials.