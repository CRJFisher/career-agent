# MCP Integration Guide

**Date**: 2025-08-03  
**Version**: 1.0  
**Status**: Implementation Complete

## Overview

The Career Application Agent now supports the Model Context Protocol (MCP), allowing it to be used as a sub-agent within Claude Desktop, Cursor IDE, and other MCP-compatible AI assistants. This integration enables powerful career assistance capabilities without requiring users to manage API keys.

## Key Features

### Dual-Mode Operation

1. **MCP Sampling Mode** (when running as MCP server):
   - All LLM operations delegated to the client via sampling requests
   - No API keys required - uses the client's LLM
   - Human-in-the-loop approval for all AI operations
   - Seamless integration with Claude Desktop

2. **Standalone Mode** (traditional operation):
   - Direct API calls using configured tokens
   - Full programmatic control
   - No human approval needed
   - Backward compatible with existing workflows

### Exposed Capabilities

The MCP server exposes five main tools:

1. **build_career_database**: Scan documents and build career database
2. **analyze_job**: Analyze job postings and assess fit
3. **generate_cv**: Create tailored CVs for specific jobs
4. **generate_cover_letter**: Generate compelling cover letters
5. **full_application_workflow**: Complete end-to-end application process

## Installation

### Prerequisites

```bash
# Install the career agent (if not already done)
cd /path/to/career-agent
pip install -e .

# Install MCP dependencies
pip install fastmcp
```

### Claude Desktop Configuration

1. Locate your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the career agent server configuration:

```json
{
  "mcpServers": {
    "career-agent": {
      "command": "python",
      "args": [
        "/path/to/career-agent/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/career-agent"
      }
    }
  }
}
```

3. Restart Claude Desktop to load the new server

## Usage in Claude Desktop

Once configured, you can use the career agent within Claude Desktop:

### Example Prompts

1. **Build Career Database**:
   ```
   Use the career agent to build my career database from documents in ~/Documents/Resume
   ```

2. **Analyze a Job**:
   ```
   Use the career agent to analyze this job posting: https://example.com/jobs/senior-engineer
   ```

3. **Generate Application Documents**:
   ```
   Help me apply to the software engineer role at TechCo using the career agent
   ```

4. **Complete Workflow**:
   ```
   Run the full application workflow for this job: [URL]
   ```

### Resource Access

The MCP server also exposes resources that Claude can access:

- `career-database://current` - Your current career database
- `documents://cv/latest` - Most recent CV
- `documents://cover-letter/latest` - Most recent cover letter

## How Sampling Works

When running as an MCP server, the agent uses sampling to request LLM completions:

1. **Agent requests completion**: The career agent needs to analyze something
2. **Claude shows prompt**: You see what the agent wants to send to the LLM
3. **You approve/edit**: You can modify or deny the request
4. **LLM processes**: If approved, Claude's LLM generates the response
5. **Agent continues**: The agent receives the response and continues

This ensures you maintain full control over:
- What information the agent processes
- How much computation is used
- What responses are generated

## Standalone Usage

The agent can still be used standalone with API keys:

```python
from flow import ApplicationFlow
from utils.adaptive_llm_wrapper import AdaptiveLLMWrapper

# Create wrapper in standalone mode (no MCP context)
llm = AdaptiveLLMWrapper()

# Use normally with your flows
flow = ApplicationFlow(llm_wrapper=llm)
result = flow.run(shared_data)
```

## Advanced Integration

### Custom MCP Clients

You can integrate the career agent into your own MCP clients:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to the career agent server
async def run_career_agent():
    server_params = StdioServerParameters(
        command="python",
        args=["/path/to/career-agent/mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # Call a tool
            result = await session.call_tool(
                "analyze_job",
                arguments={
                    "job_url": "https://example.com/job",
                    "job_description": "Optional description"
                }
            )
            
            print(result)
```

### Programmatic Dual-Mode Usage

```python
from utils.adaptive_llm_wrapper import AdaptiveLLMWrapper

# Detect mode based on context
def create_llm_wrapper(mcp_context=None):
    wrapper = AdaptiveLLMWrapper(mcp_context)
    
    if wrapper.is_mcp_mode():
        print("Running in MCP mode - no API keys needed")
    else:
        print("Running in standalone mode - using API keys")
    
    return wrapper
```

## Security Considerations

### MCP Mode Security

- **Human approval required**: Every LLM request needs your approval
- **No stored credentials**: No API keys stored in MCP mode
- **Transparent operations**: You see all prompts before they're sent
- **Local execution**: All processing happens on your machine

### Standalone Mode Security

- **API key management**: Keys stored in environment variables
- **No external access**: Agent doesn't make unauthorized requests
- **Local data storage**: All generated content stored locally

## Troubleshooting

### Common Issues

1. **"FastMCP not installed"**
   ```bash
   pip install fastmcp
   ```

2. **"No career database found"**
   - First run `build_career_database` with your documents directory
   - Database stored in `~/.career-agent/career_database.yaml`

3. **"Sampling request denied"**
   - This happens when you deny an MCP sampling request
   - The agent will handle this gracefully and report the error

4. **Claude Desktop doesn't show the agent**
   - Check your config file path and syntax
   - Ensure Python path is correct
   - Restart Claude Desktop

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

### For MCP Mode

1. **Batch Operations**: Minimize sampling requests by planning workflows
2. **Clear Context**: Provide clear job URLs and descriptions
3. **Review Prompts**: Check sampling requests before approving
4. **Cache Results**: The agent caches results to avoid repeated requests

### For Standalone Mode

1. **Secure API Keys**: Use environment variables, not hardcoded values
2. **Rate Limiting**: Built-in rate limiting prevents API abuse
3. **Error Handling**: The agent handles API errors gracefully
4. **Cost Management**: Use caching to reduce API costs

## Architecture

### Component Overview

```
┌─────────────────────┐     ┌──────────────────┐
│   Claude Desktop    │     │  Standalone App  │
│   (MCP Client)      │     │                  │
└──────────┬──────────┘     └────────┬─────────┘
           │                         │
           │ MCP Protocol            │ Direct API
           │                         │
┌──────────▼──────────────────────────▼─────────┐
│          AdaptiveLLMWrapper                   │
│  ┌─────────────┐        ┌──────────────────┐ │
│  │ MCP Sampling│        │ Direct API Calls │ │
│  └─────────────┘        └──────────────────┘ │
└───────────────────────┬───────────────────────┘
                        │
                ┌───────▼────────┐
                │ Career Agent   │
                │ Nodes & Flows  │
                └────────────────┘
```

### Key Components

1. **MCP Server** (`mcp_server.py`):
   - Exposes tools and resources via MCP
   - Handles client connections
   - Routes requests to appropriate nodes

2. **Adaptive LLM Wrapper** (`utils/adaptive_llm_wrapper.py`):
   - Detects execution context
   - Routes LLM calls appropriately
   - Maintains compatible interface

3. **Career Agent Core**:
   - Unchanged business logic
   - Works identically in both modes
   - All existing features available

## Future Enhancements

1. **Streaming Responses**: Add streaming support for long operations
2. **Progress Indicators**: Better progress reporting in MCP mode
3. **Batch Approvals**: Allow bulk approval of similar requests
4. **Context Caching**: Smarter caching of MCP sampling results
5. **Additional Tools**: Expose more fine-grained capabilities

## Conclusion

The MCP integration makes the Career Application Agent more accessible and secure. Users can leverage powerful AI assistance for job applications without managing API keys, while maintaining full control over AI operations. The dual-mode architecture ensures flexibility for different use cases while preserving all existing functionality.