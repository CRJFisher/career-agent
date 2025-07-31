# Testing Strategy for Career Agent

## Overview

This document outlines the comprehensive testing strategy for the Career Agent project. All tasks have been updated to include specific testing requirements to ensure code quality, reliability, and maintainability.

## Testing Philosophy

1. **Test-Driven Development**: Write tests alongside or before implementation
2. **Comprehensive Coverage**: Target 80%+ code coverage for all modules
3. **Isolation**: Use mocks to isolate units under test
4. **Real-World Scenarios**: Test both happy paths and edge cases
5. **Performance**: Include performance tests for critical paths

## Testing Levels

### 1. Unit Testing

**Scope**: Individual functions, methods, and classes

**Requirements**:
- All public methods must have unit tests
- Mock external dependencies (LLMs, file I/O, network)
- Test error handling and edge cases
- Minimum 80% code coverage

**Example Tasks**:
- Node implementations (tasks 5, 9-11, 13-16, 19, 22-23, 26-27)
- Utility modules (tasks 3, 13-14, 32-33)

### 2. Integration Testing

**Scope**: Multiple components working together

**Requirements**:
- Test data flow between nodes
- Verify flow execution with real node interactions
- Test error propagation and recovery
- Validate shared store consistency

**Example Tasks**:
- Flow implementations (tasks 8, 12, 17, 20, 24, 28)
- Main orchestrator (task 30)

### 3. End-to-End Testing

**Scope**: Complete pipeline from input to output

**Requirements**:
- Test full job application processing
- Verify output quality and format
- Performance benchmarking
- Real-world job description scenarios

**Example Tasks**:
- Integration test suite (task 34)
- Main orchestrator (task 30)

## Testing Patterns

### Mock-Based Testing

```python
# Example: Mocking LLM calls
with patch('utils.llm_wrapper.get_default_llm_wrapper') as mock_llm:
    mock_llm.return_value.call_llm = AsyncMock(
        return_value="mocked response"
    )
    # Test node behavior
```

### Fixture-Based Testing

```python
@pytest.fixture
def sample_career_db():
    return {
        "personal_info": {...},
        "experience": [...],
        "skills": {...}
    }
```

### Async Testing

```python
@pytest.mark.asyncio
async def test_async_node_execution():
    node = MyNode()
    result = await node.execute(store)
    assert result['status'] == 'success'
```

## Task-Specific Testing Requirements

### Node Implementation Tasks

All node tasks include:
1. Unit tests for execute() method
2. Tests for shared store interactions
3. Error handling tests
4. Mock-based testing for dependencies
5. Edge case coverage

### Flow Implementation Tasks

All flow tasks include:
1. Unit tests for flow initialization
2. Integration tests for node coordination
3. Data flow validation tests
4. Error propagation tests
5. Performance tests for execution time

### Schema/Design Tasks

Schema tasks include:
1. Validation tests for data structures
2. Schema compliance tests
3. Example validation tests
4. Format verification tests

### Infrastructure Tasks

Infrastructure tasks include:
1. API abstraction tests
2. Retry mechanism tests
3. Configuration tests
4. Performance tests
5. Integration tests with real services

## Testing Tools and Libraries

### Required Dependencies

```python
# In requirements.txt
pytest>=7.4.0          # Testing framework
pytest-asyncio>=0.21.0 # Async test support
pytest-cov>=4.0.0      # Coverage reporting
pytest-mock>=3.10.0    # Enhanced mocking
```

### Recommended Tools

- **Coverage.py**: Code coverage measurement
- **pytest-benchmark**: Performance testing
- **pytest-timeout**: Prevent hanging tests
- **responses**: Mock HTTP requests
- **freezegun**: Mock time/dates

## Test Organization

```
tests/
├── unit/                 # Unit tests
│   ├── nodes/           # Node tests
│   ├── flows/           # Flow tests
│   └── utils/           # Utility tests
├── integration/         # Integration tests
├── fixtures/            # Shared test data
└── conftest.py         # Pytest configuration
```

## Continuous Integration

### Pre-commit Checks

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: tests
      name: Run tests
      entry: pytest
      language: system
      types: [python]
      pass_filenames: false
```

### CI Pipeline

```yaml
# Example GitHub Actions
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
    - name: Install dependencies
      run: pip install -e ".[dev]"
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Performance Testing

### Requirements

- Main orchestrator must process job application in < 60 seconds
- Individual nodes must execute in < 10 seconds
- Flow coordination overhead < 5% of total time

### Benchmarking

```python
@pytest.mark.benchmark
def test_node_performance(benchmark):
    result = benchmark(node.execute, store)
    assert result['status'] == 'success'
```

## Test Data Management

### Fixtures

- Career database examples
- Job description samples
- Expected output templates
- Error scenarios

### Data Sources

1. `examples/` directory for reference data
2. Fixtures in test files for specific scenarios
3. Mock data generators for edge cases

## Quality Metrics

### Coverage Goals

- Overall: 80% minimum
- Critical paths: 95% minimum
- Error handling: 100%

### Test Execution

- All tests must pass before merge
- No flaky tests allowed
- Test execution time < 5 minutes

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Arrange-Act-Assert**: Follow AAA pattern for test structure
3. **One Assertion**: Each test should verify one behavior
4. **Independent Tests**: Tests should not depend on execution order
5. **Clean State**: Each test should start with clean state
6. **Meaningful Failures**: Test failures should clearly indicate the problem

## Conclusion

This comprehensive testing strategy ensures that the Career Agent system is robust, reliable, and maintainable. By following these guidelines, we achieve high quality code that can be confidently modified and extended.