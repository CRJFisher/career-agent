# LLM Response Caching

The Career Application Agent includes an optional caching layer for LLM responses to improve development speed and reduce API costs.

## Overview

LLM caching stores responses from language model API calls and reuses them when identical requests are made. This is particularly useful during:

- Development and testing
- Debugging the same workflow multiple times
- Running integration tests
- Working offline with previously cached responses

## Configuration

### Enabling Cache

Set the environment variable to enable caching:

```bash
export ENABLE_LLM_CACHE=true
```

### Cache Settings

Configure cache behavior with these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_LLM_CACHE` | `false` | Enable/disable caching |
| `LLM_CACHE_BACKEND` | `disk` | Cache backend (`disk`, `memory`, `disabled`) |
| `LLM_CACHE_DIR` | `.llm_cache` | Directory for disk cache |
| `LLM_CACHE_TTL` | `604800` | Cache TTL in seconds (default: 1 week) |

### Example Configuration

```bash
# Enable caching with custom settings
export ENABLE_LLM_CACHE=true
export LLM_CACHE_BACKEND=disk
export LLM_CACHE_DIR=~/.career_agent/cache
export LLM_CACHE_TTL=86400  # 24 hours
```

## Cache Management

### Command Line Tool

Use the cache management CLI to inspect and manage the cache:

```bash
# Show cache statistics
python -m utils.llm_cache_cli stats

# Clear the cache
python -m utils.llm_cache_cli clear

# Show current configuration
python -m utils.llm_cache_cli info
```

### Programmatic Access

```python
from utils.llm_wrapper import get_default_llm_wrapper

# Get wrapper with caching enabled
wrapper = get_default_llm_wrapper(use_cache=True)

# Clear cache programmatically
if hasattr(wrapper, 'clear_cache'):
    wrapper.clear_cache()

# Get cache metrics
if hasattr(wrapper, 'get_cache_metrics'):
    metrics = wrapper.get_cache_metrics()
    print(f"Cache hit rate: {metrics['hit_rate']:.1%}")
```

## Cache Key Generation

Cache keys are generated from:

- Prompt content
- System prompt (if provided)
- Model name
- Temperature setting
- Max tokens
- Any additional parameters

This ensures that different variations of the same prompt are cached separately.

## Per-Request Cache Control

You can override cache behavior for individual requests:

```python
# Force cache bypass for this request
response = wrapper.call_llm(
    prompt="Generate something random",
    use_cache=False  # Bypass cache
)

# Force cache use even if globally disabled
response = wrapper.call_llm(
    prompt="Expensive analysis",
    use_cache=True  # Use cache
)
```

## Backend Options

### Disk Cache (Default)

- Persistent across sessions
- Survives application restarts
- Configurable size limits
- Best for development

### Memory Cache

- Fastest performance
- Lost on application restart
- Good for testing
- Limited by available RAM

### Disabled

- No caching performed
- Useful for production or when fresh responses are required

## Best Practices

1. **Development**: Enable disk caching to speed up iterative development
2. **Testing**: Use memory caching for unit tests
3. **Production**: Generally disable caching or use very short TTLs
4. **CI/CD**: Consider pre-warming cache with common requests

## Performance Impact

With caching enabled:

- First request: Normal latency + small caching overhead
- Subsequent requests: Near-instant (< 10ms)
- Cache misses: No performance penalty

## Troubleshooting

### Cache Not Working

1. Verify caching is enabled:
   ```bash
   echo $ENABLE_LLM_CACHE  # Should be "true"
   ```

2. Check cache directory permissions:
   ```bash
   ls -la .llm_cache/
   ```

3. View cache statistics:
   ```bash
   python -m utils.llm_cache_cli stats
   ```

### Stale Cache Entries

If you're getting outdated responses:

1. Clear the entire cache:
   ```bash
   python -m utils.llm_cache_cli clear
   ```

2. Or reduce the TTL:
   ```bash
   export LLM_CACHE_TTL=3600  # 1 hour
   ```

### Disk Space Issues

Monitor cache size and clear periodically:

```bash
# Check size
du -sh .llm_cache/

# Clear if too large
python -m utils.llm_cache_cli clear
```

## Security Considerations

- Cache files may contain sensitive information
- Ensure cache directory has appropriate permissions
- Consider encrypting cache in production environments
- Clear cache after working with sensitive data

## Example Workflow

```bash
# 1. Enable caching for development
export ENABLE_LLM_CACHE=true

# 2. Run your workflow
python main.py analyze --job-url https://example.com/job

# 3. Check cache statistics
python -m utils.llm_cache_cli stats

# 4. Re-run workflow (will use cache)
python main.py analyze --job-url https://example.com/job

# 5. Clear cache when done
python -m utils.llm_cache_cli clear
```