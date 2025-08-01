# OpenRouter Setup Guide

## Overview

This project uses OpenRouter to provide unified access to multiple LLM providers through a single API key. OpenRouter supports models from OpenAI, Anthropic, Google, Meta, and many others, all accessible through the OpenAI SDK format.

## Setup

### 1. Get an OpenRouter API Key

1. Sign up at [openrouter.ai](https://openrouter.ai/)
2. Get your API key from the dashboard
3. Add credits to your account

### 2. Set Environment Variable

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Or add to your `.env` file:
```
OPENROUTER_API_KEY=your-api-key-here
```

## Available Models

The wrapper includes convenient aliases for popular models:

| Alias | Full Model ID | Provider |
|-------|---------------|----------|
| `gpt-4` | `openai/gpt-4` | OpenAI |
| `gpt-4-turbo` | `openai/gpt-4-turbo-preview` | OpenAI |
| `gpt-3.5-turbo` | `openai/gpt-3.5-turbo` | OpenAI |
| `claude-3-opus` | `anthropic/claude-3-opus-20240229` | Anthropic |
| `claude-3-sonnet` | `anthropic/claude-3-sonnet-20240229` | Anthropic |
| `claude-3-haiku` | `anthropic/claude-3-haiku-20240307` | Anthropic |
| `gemini-pro` | `google/gemini-pro` | Google |
| `mistral-large` | `mistralai/mistral-large` | Mistral |
| `mixtral` | `mistralai/mixtral-8x7b-instruct` | Mistral |

You can also use any model ID directly from [OpenRouter's model list](https://openrouter.ai/models).

## Usage Examples

### Basic Usage

```python
from utils.llm_wrapper import get_default_llm_wrapper

# Get the wrapper instance
llm = get_default_llm_wrapper()

# Simple completion
response = llm.call_llm(
    "What is the capital of France?",
    model="claude-3-haiku"  # Fast and cheap model
)
print(response)
```

### Structured Output

```python
# Get structured YAML output
result = llm.call_llm_structured(
    prompt="List the top 3 programming languages for web development",
    output_format="yaml",
    model="claude-3-opus"  # More capable model for structured output
)
print(result)
```

### Using in Nodes

```python
class MyNode(Node):
    def __init__(self):
        super().__init__()
        self.llm = get_default_llm_wrapper()
    
    def exec(self, prep_res):
        # Use the wrapper in your node logic
        response = self.llm.call_llm_sync(
            prompt=f"Analyze this text: {prep_res}",
            model="gpt-4",  # Choose model based on task
            temperature=0.3  # Lower for more consistent output
        )
        return response
```

## Model Selection Guidelines

### For Requirements Extraction (ExtractRequirementsNode)
- **Recommended**: `claude-3-opus` or `gpt-4`
- High accuracy needed for parsing complex job descriptions
- Structured output capability is important

### For Quick Analysis
- **Recommended**: `claude-3-haiku` or `gpt-3.5-turbo`
- Fast and cost-effective
- Good for simple classification or summarization

### For Creative Tasks (Cover Letter Generation)
- **Recommended**: `claude-3-sonnet` or `gpt-4`
- Good balance of creativity and coherence
- Higher temperature settings work well

## Cost Optimization

OpenRouter charges based on usage across all models. To optimize costs:

1. Use cheaper models (haiku, gpt-3.5-turbo) for simple tasks
2. Reserve expensive models (opus, gpt-4) for complex reasoning
3. Set appropriate `max_tokens` limits
4. Use lower temperatures for more predictable (cached) outputs

## Monitoring Usage

You can monitor your usage and costs at:
- [OpenRouter Dashboard](https://openrouter.ai/dashboard)

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ValueError: OpenRouter API key not provided or found in environment
   ```
   Solution: Ensure `OPENROUTER_API_KEY` is set in your environment

2. **Model Not Found**
   ```
   Error: Model not found
   ```
   Solution: Check the model ID is correct or use one of the predefined aliases

3. **Rate Limits**
   ```
   Error: Rate limit exceeded
   ```
   Solution: OpenRouter handles rate limits across providers. Wait and retry, or upgrade your account limits.

## Advanced Configuration

### Custom Headers

OpenRouter supports custom headers for analytics:

```python
wrapper = LLMWrapper(
    app_name="MyCustomApp",  # Shows in OpenRouter analytics
    default_model="anthropic/claude-3-sonnet-20240229"
)
```

### Direct Model Access

For models not in the alias list:

```python
response = llm.call_llm(
    "Hello",
    model="meta-llama/llama-3-70b-instruct"  # Use full model ID
)
```