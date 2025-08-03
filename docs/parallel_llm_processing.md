# Parallel LLM Processing

The Career Application Agent supports parallel LLM API calls for significant performance improvements when processing multiple documents or generating multiple outputs.

## Overview

Parallel processing reduces total processing time by executing multiple LLM calls concurrently instead of sequentially. This is particularly beneficial for:

- **Document Processing**: Extract experiences from multiple documents simultaneously
- **Batch Analysis**: Analyze multiple job requirements in parallel
- **Content Generation**: Generate CV and cover letter concurrently

## Performance Benefits

With parallel processing:
- **10 documents**: ~5x faster (10s vs 50s sequential)
- **20 documents**: ~5-10x faster (20s vs 100s sequential)
- **Scalable**: Performance improves with more documents

## Usage

### Using Async Nodes

The system provides async versions of batch processing nodes:

```python
from async_nodes import AsyncExtractExperienceNode
from utils.async_llm_wrapper import get_async_llm_wrapper

# Create async LLM wrapper
async_llm = await get_async_llm_wrapper(
    max_concurrent=5,  # Max parallel calls
    rate_limit=10,     # Requests per second
)

# Use async node
node = AsyncExtractExperienceNode(async_llm)

# Process documents in parallel
await node.run_async(shared_store)
```

### Direct Async API Usage

For custom implementations:

```python
from utils.async_llm_wrapper import AsyncLLMWrapper

async def process_documents(documents):
    async with AsyncLLMWrapper() as llm:
        # Process all documents in parallel
        prompts = [
            (f"Extract from {doc['name']}", "You are an expert...")
            for doc in documents
        ]
        
        results = await llm.call_llm_batch(prompts)
        return results
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_LLM` | `5` | Maximum concurrent LLM calls |
| `LLM_RATE_LIMIT` | `10` | Max requests per second |
| `LLM_RATE_PERIOD` | `1.0` | Rate limit period in seconds |
| `ASYNC_LLM_TIMEOUT` | `60` | Request timeout in seconds |

### Example Configuration

```bash
# Optimize for throughput
export MAX_CONCURRENT_LLM=10
export LLM_RATE_LIMIT=20

# Conservative settings
export MAX_CONCURRENT_LLM=3
export LLM_RATE_LIMIT=5
```

## Integration with Existing Nodes

### Converting BatchNode to Async

The system can automatically convert existing BatchNodes:

```python
from utils.async_batch_processor import create_async_batch_node
from nodes import ExtractExperienceNode

# Create async version of existing node
AsyncExtractExperienceNode = create_async_batch_node(
    ExtractExperienceNode,
    async_llm_wrapper,
    batch_size=5,
    max_concurrent=10
)
```

### Using in Flows

Async nodes work seamlessly with PocketFlow's AsyncFlow:

```python
from pocketflow import AsyncFlow
from async_nodes import AsyncExtractExperienceNode

class AsyncExperienceDatabaseFlow(AsyncFlow):
    def __init__(self):
        # Use async nodes
        extract = AsyncExtractExperienceNode()
        self.start(extract)
```

## Rate Limiting

The async wrapper includes built-in rate limiting to respect API limits:

### Token Bucket Algorithm
- Allows burst up to the rate limit
- Smooths requests over time
- Prevents API throttling

### Automatic Backoff
- Handles rate limit errors gracefully
- Exponential backoff on failures
- Configurable retry attempts

## Best Practices

### 1. Choose Appropriate Concurrency

```python
# For document processing (I/O heavy)
max_concurrent = 10

# For complex analysis (compute heavy)
max_concurrent = 5

# For rate-limited APIs
max_concurrent = 3
```

### 2. Monitor API Usage

```python
# The async wrapper logs all calls
import logging
logging.getLogger("utils.async_llm_wrapper").setLevel(logging.INFO)
```

### 3. Handle Errors Gracefully

```python
try:
    results = await llm.call_llm_batch(prompts)
except Exception as e:
    # Fallback to sequential processing
    results = []
    for prompt in prompts:
        try:
            result = await llm.call_llm(prompt[0])
            results.append(result)
        except:
            results.append(None)
```

### 4. Use Caching with Async

Caching works seamlessly with async calls:

```python
# Enable caching for async calls
export ENABLE_LLM_CACHE=true

# Async wrapper will use cache automatically
async_llm = await get_async_llm_wrapper(use_cache=True)
```

## Performance Benchmarking

Run the benchmark to test performance:

```bash
# Basic benchmark
python tests/benchmark_parallel_llm.py

# Test with 50 documents
python tests/benchmark_parallel_llm.py --documents 50

# Compare different batch sizes
python tests/benchmark_parallel_llm.py --compare-batch-sizes
```

### Example Results

```
Documents processed: 20
Sequential time: 100.00s
Parallel time: 20.50s
Speedup: 4.9x faster
Time saved: 79.50s (80%)
```

## Troubleshooting

### High Memory Usage

Reduce concurrency:
```python
AsyncLLMWrapper(max_concurrent=3)
```

### Rate Limit Errors

Adjust rate limiting:
```python
AsyncLLMWrapper(
    rate_limit=5,      # Fewer requests
    rate_period=2.0    # Over longer period
)
```

### Timeout Errors

Increase timeout for large documents:
```python
AsyncLLMWrapper(timeout=120.0)  # 2 minutes
```

### Connection Errors

The wrapper includes automatic retry:
```python
# Retry configuration in AsyncParallelBatchNode
node = AsyncExtractExperienceNode()
node.max_retries = 5
node.wait = 2  # Seconds between retries
```

## Examples

### Example 1: Parallel Document Extraction

```python
async def extract_all_experiences(document_paths):
    # Initialize
    async with AsyncLLMWrapper() as llm:
        node = AsyncExtractExperienceNode(llm)
        
        # Prepare shared store
        shared = {
            "document_sources": [
                {"path": p, "name": os.path.basename(p)}
                for p in document_paths
            ]
        }
        
        # Process in parallel
        await node.run_async(shared)
        
        # Results in shared["extracted_experiences"]
        return shared["extracted_experiences"]
```

### Example 2: Concurrent Generation

```python
async def generate_application_docs(job_data):
    async with AsyncLLMWrapper(max_concurrent=2) as llm:
        # Generate CV and cover letter concurrently
        cv_task = llm.call_llm(
            f"Generate CV for {job_data['position']}",
            system_prompt="You are a CV expert..."
        )
        
        letter_task = llm.call_llm(
            f"Generate cover letter for {job_data['company']}",
            system_prompt="You are a cover letter expert..."
        )
        
        cv, letter = await asyncio.gather(cv_task, letter_task)
        return {"cv": cv, "cover_letter": letter}
```

### Example 3: Batch Job Analysis

```python
async def analyze_multiple_jobs(job_urls):
    async with AsyncLLMWrapper() as llm:
        # Prepare analysis prompts
        prompts = [
            (f"Extract requirements from: {url}", 
             "Extract job requirements as structured data")
            for url in job_urls
        ]
        
        # Analyze all jobs in parallel
        requirements = await llm.call_llm_batch(
            prompts,
            temperature=0.3,
            output_format="yaml"
        )
        
        return dict(zip(job_urls, requirements))
```