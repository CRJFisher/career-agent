# MCP Sampling Research

**Date**: 2025-08-03  
**Author**: Career Application Agent Team  
**Purpose**: Research MCP sampling functionality for implementing dual-mode LLM operations

## Overview

Model Context Protocol (MCP) sampling allows servers to request LLM completions through the client, enabling sophisticated agentic behaviors while maintaining security and privacy. This is crucial for our implementation as it allows the career agent to operate without its own API keys when running as an MCP server.

## Key Concepts

### What is MCP Sampling?

Sampling is a feature where:
- **Servers** can request AI completions from the **client's** LLM
- The client maintains control over model access and permissions
- No server API keys are necessary
- Human-in-the-loop approval is required for security

### Request Flow

1. **Server initiates**: Server sends a `sampling/createMessage` request
2. **Client reviews**: Client presents the request to the user
3. **User approval**: User can edit or reject the prompt
4. **LLM interaction**: If approved, client sends to LLM
5. **Final review**: Client shows output to user
6. **Response**: Approved result returned to server

## Technical Implementation

### Request Structure

```json
{
  "method": "sampling/createMessage",
  "params": {
    "messages": [
      {
        "role": "user",
        "content": {
          "type": "text",
          "text": "Analyze this job description and extract key requirements"
        }
      }
    ],
    "systemPrompt": "You are a career application assistant.",
    "includeContext": "thisServer",
    "maxTokens": 1000
  }
}
```

### Response Structure

```json
{
  "role": "assistant",
  "content": {
    "type": "text",
    "text": "Based on the job description, the key requirements are..."
  }
}
```

### Python Implementation Example

```python
from mcp import types
from mcp.server import Server
import asyncio

class CareerAgentMCPServer:
    def __init__(self):
        self.server = Server("career-agent")
        
    async def request_llm_completion(self, prompt: str, system_prompt: str = None):
        """Request LLM completion through MCP sampling."""
        # Create the sampling request
        messages = [
            types.SamplingMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=prompt
                )
            )
        ]
        
        # Send sampling request to client
        result = await self.server.request_sampling(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=1500
        )
        
        return result.content.text
```

## Integration Strategy

### Dual-Mode Architecture

Our implementation needs to support two modes:

1. **MCP Mode** (Server running under MCP client):
   - All LLM calls go through `sampling/createMessage`
   - No API keys needed
   - Human approval for each request
   - Client controls model selection

2. **Standalone Mode** (Direct execution):
   - Use existing `LLMWrapper` with API keys
   - Direct API calls to OpenRouter
   - Full programmatic control
   - No human approval needed

### Adaptive LLM Wrapper Design

```python
class AdaptiveLLMWrapper:
    """Wrapper that adapts between MCP sampling and direct API calls."""
    
    def __init__(self, mcp_server=None):
        self.mcp_server = mcp_server
        self.standalone_wrapper = None
        
        if not mcp_server:
            # Standalone mode
            from utils.llm_wrapper import get_default_llm_wrapper
            self.standalone_wrapper = get_default_llm_wrapper()
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using appropriate method."""
        if self.mcp_server:
            # MCP mode - use sampling
            return await self._mcp_generate(prompt, **kwargs)
        else:
            # Standalone mode - direct API
            return await self.standalone_wrapper.generate(prompt, **kwargs)
    
    async def _mcp_generate(self, prompt: str, **kwargs) -> str:
        """Generate using MCP sampling."""
        messages = [
            {
                "role": "user",
                "content": {"type": "text", "text": prompt}
            }
        ]
        
        # Request sampling from client
        response = await self.mcp_server.request_sampling(
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 1500),
            temperature=kwargs.get("temperature", 0.7)
        )
        
        return response.content.text
```

## Security Considerations

### Human-in-the-Loop

MCP specification states: "There SHOULD always be a human in the loop with the ability to deny sampling requests."

This means:
- Every LLM request will prompt the user
- Users can review and edit prompts
- Users can deny requests
- This is by design for security

### Best Practices

1. **Clear Prompts**: Make sampling requests clear about intent
2. **Minimal Requests**: Batch operations where possible
3. **Context Management**: Use `includeContext` wisely
4. **Error Handling**: Handle denied requests gracefully

## Implementation Challenges

### 1. Asynchronous Nature

All MCP operations are async, which aligns well with our existing async nodes but requires careful handling.

### 2. Human Approval Latency

Each sampling request requires human approval, which could slow down workflows. Mitigation:
- Batch related requests
- Provide clear context for approval
- Cache responses where appropriate

### 3. Context Limits

Sampling requests have token limits. Need to:
- Chunk large prompts
- Summarize context when needed
- Use structured prompts efficiently

## Testing Strategy

### Mock MCP Server

```python
class MockMCPServer:
    """Mock MCP server for testing."""
    
    async def request_sampling(self, messages, **kwargs):
        # Return predetermined responses for testing
        prompt = messages[0]["content"]["text"]
        
        if "analyze job" in prompt:
            return types.CreateMessageResult(
                role="assistant",
                content=types.TextContent(
                    type="text",
                    text="Mock job analysis response"
                )
            )
        
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text="Mock default response"
            )
        )
```

### Integration Tests

1. Test dual-mode switching
2. Test sampling request format
3. Test error handling (denied requests)
4. Test context inclusion
5. Test token limits

## Benefits of MCP Sampling

### For Users

1. **No API Keys**: Users don't need to manage LLM API keys
2. **Cost Control**: Billing through their existing LLM provider
3. **Model Choice**: Use whatever model they prefer
4. **Privacy**: Full control over what the agent sees

### For Developers

1. **Simplified Distribution**: No API key management
2. **Flexibility**: Works with any LLM the client supports
3. **Security**: No credentials to secure
4. **Standardization**: Follow industry protocol

## Current Limitations

1. **Claude Desktop**: Sampling not yet supported (as of research date)
2. **Approval Fatigue**: Many requests could overwhelm users
3. **Performance**: Human approval adds latency
4. **Testing**: Harder to automate tests with human-in-loop

## Conclusion

MCP sampling provides an elegant solution for our dual-mode requirement. By implementing an adaptive wrapper, we can support both:
- Seamless integration as an MCP server (no API keys)
- Standalone operation with direct API access

The key is designing our nodes to work efficiently within the constraints of human-approved sampling while maintaining the same functionality in standalone mode.