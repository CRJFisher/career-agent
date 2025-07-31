# Developer Quick Reference Guide

## Getting Started

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database_parser.py

# Run with coverage
pytest --cov=.
```

## Project Structure

### Core Modules

#### `nodes.py`
- **Base Class**: `Node` - Abstract base for all nodes
- **Key Method**: `async execute(store: Dict) -> Dict`
- **Implemented Nodes**:
  - `ExtractRequirementsNode`: Extracts structured requirements from job descriptions

#### `flow.py`
- **Base Class**: `Flow` - Orchestrates node execution
- **Key Methods**:
  - `add_node()`: Add node to flow
  - `add_edge()`: Connect nodes
  - `async execute()`: Run the flow
- **Implemented Flows**:
  - `RequirementExtractionFlow`: Single-node flow for requirements extraction

#### `utils/llm_wrapper.py`
- **Main Class**: `LLMWrapper` - Unified LLM interface
- **Key Methods**:
  - `async call_llm()`: Basic LLM call
  - `async call_llm_structured()`: Get structured output (YAML/JSON)
- **Providers**: OpenAI, Anthropic

#### `utils/database_parser.py`
- **Main Function**: `load_career_database(path)` - Load YAML files
- **Features**:
  - Single file or directory support
  - Validation and merging
  - Comprehensive error handling

## Common Tasks

### Adding a New Node

1. Create class inheriting from `Node`:
```python
class MyNewNode(Node):
    def __init__(self):
        super().__init__(name="MyNewNode")
    
    async def execute(self, store: Dict[str, Any]) -> Dict[str, Any]:
        # Get input from store
        input_data = store.get('input_key')
        
        # Process data
        result = await self.process(input_data)
        
        # Return updates to store
        return {
            'output_key': result,
            'status': 'success'
        }
```

2. Add tests in `tests/test_my_new_node.py`

### Adding a New Flow

1. Create class inheriting from `Flow`:
```python
class MyNewFlow(Flow):
    def __init__(self):
        super().__init__(name="MyNewFlow")
        self._setup_flow()
    
    def _setup_flow(self):
        # Add nodes
        self.add_node(Node1())
        self.add_node(Node2())
        
        # Define edges
        self.add_edge("Node1", "Node2")
```

### Working with LLMs

```python
# Get LLM wrapper
llm = get_default_llm_wrapper()

# Basic call
response = await llm.call_llm(
    prompt="Extract key points",
    system_prompt="You are a helpful assistant",
    temperature=0.7
)

# Structured output
data = await llm.call_llm_structured(
    prompt="Extract as YAML",
    output_format="yaml",
    temperature=0.3
)
```

### Loading Career Data

```python
from utils.database_parser import load_career_database

# Load single file
data = load_career_database("career.yaml")

# Load directory
data = load_career_database("career_data/")

# Validate
warnings = validate_career_database(data)
```

## Data Schemas

### Career Database Structure
```yaml
personal_info:
  name: string
  email: string
  phone: string
  location: string

experience:
  - title: string
    company: string
    duration: string
    achievements: [string]
    technologies: [string]

skills:
  technical: [string]
  soft: [string]
```

### Job Requirements Structure
```yaml
role_summary:
  title: string
  company: string
  location: string
  type: string
  level: string

hard_requirements:
  education: [string]
  experience:
    years_required: number
    specific_experience: [string]
  technical_skills:
    programming_languages: [string]
    technologies: [string]

responsibilities:
  primary: [string]
  secondary: [string]
```

## Testing Guidelines

### Unit Test Structure
```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestMyComponent:
    @pytest.mark.asyncio
    async def test_success_case(self):
        # Arrange
        mock_dep = Mock()
        component = MyComponent(mock_dep)
        
        # Act
        result = await component.method()
        
        # Assert
        assert result['status'] == 'success'
```

### Mocking LLM Calls
```python
with patch('module.get_default_llm_wrapper') as mock_llm:
    mock_llm.return_value.call_llm_structured = AsyncMock(
        return_value={'key': 'value'}
    )
    # Test code
```

## Best Practices

### Code Style
- Use type hints everywhere
- Add comprehensive docstrings
- Follow PEP 8 (enforced by black/ruff)
- Keep functions focused and small

### Error Handling
```python
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return {'status': 'failed', 'error': str(e)}
except Exception as e:
    logger.exception("Unexpected error")
    return {'status': 'error', 'error': str(e)}
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Starting process")
logger.warning(f"Validation warning: {warning}")
logger.error(f"Process failed: {error}")
```

## Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Store Contents
```python
# In a node
logger.debug(f"Store contents: {store}")

# In a flow
print(f"Final store: {self.store}")
```

### Test Individual Components
```python
# Test a node directly
node = ExtractRequirementsNode()
result = await node.execute({'job_description': 'test'})

# Test LLM wrapper
llm = LLMWrapper(provider="openai")
response = await llm.call_llm("test prompt")
```

## Common Issues

### "No module named 'utils'"
- Make sure you're in the project root
- Install in editable mode: `pip install -e .`

### LLM API Errors
- Check API keys are set correctly
- Verify internet connection
- Check API rate limits

### YAML Parsing Errors
- Validate YAML syntax (indentation!)
- Use a YAML linter
- Check for special characters

## Resources

- **Backlog Tasks**: `backlog task list --plain`
- **Schema Docs**: `docs/*_schema.md`
- **Design Doc**: `docs/design.md`
- **Examples**: `examples/`