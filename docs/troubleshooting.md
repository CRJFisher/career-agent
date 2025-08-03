# Troubleshooting Guide

Common issues and solutions for the Career Application Agent.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [API and Authentication](#api-and-authentication)
3. [Document Processing](#document-processing)
4. [LLM Issues](#llm-issues)
5. [Checkpoint and Resume](#checkpoint-and-resume)
6. [Performance Issues](#performance-issues)
7. [Common Errors](#common-errors)
8. [Debug Mode](#debug-mode)

## Installation Issues

### Python Version Mismatch

**Problem**: `SyntaxError` or import errors

**Solution**:
```bash
# Check Python version (requires 3.8+)
python --version

# Use specific Python version
python3.8 -m venv venv
```

### Missing Dependencies

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall all dependencies
pip install --upgrade pip
pip install -r requirements.txt

# For development
pip install -e ".[dev]"
```

### Virtual Environment Issues

**Problem**: Packages not found despite installation

**Solution**:
```bash
# Ensure venv is activated
which python  # Should show venv path

# Reactivate
deactivate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

## API and Authentication

### OpenRouter API Key Not Found

**Problem**: `KeyError: 'OPENROUTER_API_KEY'`

**Solution**:
```bash
# Set environment variable
export OPENROUTER_API_KEY="your-key-here"

# Or use .env file
echo "OPENROUTER_API_KEY=your-key-here" >> .env
```

### API Rate Limits

**Problem**: `429 Too Many Requests`

**Solution**:
```python
# Adjust retry settings in utils/llm_wrapper.py
LLM_CONFIG = {
    "retry_wait": 5.0,  # Increase wait time
    "max_retries": 5
}
```

### Invalid API Key

**Problem**: `401 Unauthorized`

**Solution**:
```bash
# Test API key
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Document Processing

### PDF Parsing Errors

**Problem**: `PDFReadError` or garbled text

**Solution**:
```bash
# Install optional PDF dependencies
pip install pypdf2 pdfplumber

# For OCR support
pip install pytesseract
```

### Google Drive Access Denied

**Problem**: `403 Forbidden` when accessing Google Drive

**Solution**:
1. Check credentials file exists
2. Verify OAuth scopes include Drive access
3. Re-authenticate:
```python
from utils.google_drive_auth import authenticate
authenticate(force_reauth=True)
```

### Large File Handling

**Problem**: `MemoryError` with large documents

**Solution**:
```bash
# Process in smaller batches
python main.py build-database \
  --batch-size 3 \
  --max-file-size 10MB
```

## LLM Issues

### Model Not Available

**Problem**: `Model anthropic/claude-3-5-sonnet not available`

**Solution**:
```python
# Check available models
from utils.llm_wrapper import list_available_models
print(list_available_models())

# Use alternative model
export DEFAULT_LLM_MODEL="anthropic/claude-3-haiku"
```

### Context Length Exceeded

**Problem**: `Context length exceeded`

**Solution**:
```python
# Reduce document chunk size
EXTRACTION_CONFIG = {
    "chunk_size": 2000,  # Reduce from default
    "overlap": 200
}
```

### Inconsistent LLM Responses

**Problem**: Different results on each run

**Solution**:
```python
# Reduce temperature for consistency
llm = get_default_llm_wrapper()
llm.temperature = 0.1  # More deterministic
```

## Checkpoint and Resume

### Checkpoint Not Found

**Problem**: `FileNotFoundError: No checkpoints found`

**Solution**:
```bash
# List available checkpoints
ls -la checkpoints/*/

# Specify checkpoint explicitly
python main.py resume --checkpoint analysis_20240115_123456
```

### Corrupted Checkpoint

**Problem**: `yaml.YAMLError` when loading checkpoint

**Solution**:
```bash
# Use backup
cp checkpoints/flow/checkpoint_latest.yaml.bak \
   checkpoints/flow/checkpoint_latest.yaml

# Or start fresh
rm -rf checkpoints/flow/
```

### User Edits Not Applied

**Problem**: Changes to output files ignored

**Solution**:
1. Ensure editing correct file in `outputs/`
2. Save file before resuming
3. Check for YAML syntax errors:
```bash
python -m yaml outputs/analysis_output.yaml
```

## Performance Issues

### Slow Document Processing

**Problem**: Takes too long to process documents

**Solution**:
```python
# Enable parallel processing
flow = ExperienceDatabaseFlow(config={
    "parallel_extraction": True,
    "num_workers": 4
})
```

### High Memory Usage

**Problem**: System runs out of memory

**Solution**:
```bash
# Monitor memory
python -m memory_profiler main.py build-database

# Limit concurrent processing
export MAX_CONCURRENT_DOCS=2
```

### Slow LLM Responses

**Problem**: Long wait times for LLM

**Solution**:
```python
# Use faster model for development
export DEFAULT_LLM_MODEL="gpt-3.5-turbo"

# Enable caching
export ENABLE_LLM_CACHE=true
```

## Common Errors

### ValidationError

**Problem**: `ValidationError: Invalid career database schema`

**Solution**:
```python
# Validate and fix
from utils.career_database_parser import validate_career_database

db = load_career_database("career.yaml")
errors = validate_career_database(db)
print(errors)  # See specific issues
```

### Network Timeouts

**Problem**: `TimeoutError` during web research

**Solution**:
```python
# Increase timeout
WEB_CONFIG = {
    "timeout": 30,  # seconds
    "retry_count": 3
}
```

### File Permission Errors

**Problem**: `PermissionError: [Errno 13]`

**Solution**:
```bash
# Check file permissions
ls -la outputs/

# Fix permissions
chmod 644 outputs/*.yaml
```

## Debug Mode

### Enable Verbose Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Trace Node Execution

```python
# Add to any node
class MyNode(Node):
    def prep(self, shared):
        logger.debug(f"Prep input keys: {list(shared.keys())}")
        result = {...}
        logger.debug(f"Prep output: {result}")
        return result
```

### Save Intermediate States

```python
# Enable debug checkpoints
flow = AnalysisFlow(debug_checkpoints=True)
```

### Common Debug Commands

```bash
# Test specific node
python -m pytest tests/test_nodes.py::TestExtractRequirementsNode -v

# Profile performance
python -m cProfile -s cumulative main.py apply --job-url "..."

# Check shared store state
python -c "import yaml; print(yaml.safe_load(open('checkpoints/analysis/latest.yaml')))"
```

## Getting Help

### Logs Location

- Application logs: `logs/career_agent.log`
- Error logs: `logs/errors.log`
- Debug dumps: `debug/`

### Diagnostic Script

```bash
# Run diagnostics
python scripts/diagnose.py

# Output includes:
# - Python version
# - Installed packages
# - API connectivity
# - File permissions
# - System resources
```

### Community Support

1. Check existing issues on GitHub
2. Join Discord community
3. Stack Overflow tag: `career-agent`

### Reporting Bugs

Include:
1. Error message and stack trace
2. Steps to reproduce
3. Environment (OS, Python version)
4. Relevant configuration
5. Sample input data (sanitized)