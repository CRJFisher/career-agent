---
id: task-51
title: Implement MCP server integration
status: Todo
assignee: []
created_date: '2025-08-03'
updated_date: '2025-08-03'
labels: [enhancement, integration, mcp]
dependencies: []
---

## Description

Create a Model Context Protocol (MCP) server to expose the Career Application Agent as a sub-agent that can be used by other AI assistants like Claude Code. MCP is an open standard by Anthropic that standardizes how applications provide context to LLMs, essentially acting as a "USB-C port for AI applications". This would allow the career agent's capabilities to be seamlessly integrated into coding workflows, IDEs, and other AI-powered tools.

**Critical**: The implementation must leverage the MCP `sampling` protocol, which allows the server to request that the client performs LLM tasks. This is essential because the career agent relies heavily on LLM calls for analysis, content generation, and decision-making. Instead of requiring its own LLM configuration, the MCP server will delegate all LLM operations to the client through sampling requests.

## Acceptance Criteria

- [ ] Research and understand MCP specification, especially the sampling protocol
- [ ] Install MCP Python SDK (`pip install mcp`)
- [ ] Create `mcp_server.py` that exposes career agent as MCP server
- [ ] **Implement MCP sampling for all LLM operations**:
  - Replace direct LLM calls with sampling requests
  - Maintain conversation context across sampling calls
  - Handle sampling responses and errors appropriately
- [ ] Implement MCP tools for key capabilities:
  - Build career database from documents
  - Analyze job requirements
  - Generate tailored CV/cover letter
  - Research company information
  - Get application recommendations
- [ ] Add MCP resources for:
  - Career database access
  - Generated documents
  - Analysis results
- [ ] Create MCP prompts for common workflows
- [ ] Implement proper error handling and logging
- [ ] Add configuration for MCP server settings
- [ ] Create integration tests for MCP endpoints
- [ ] Write documentation for MCP usage and sampling
- [ ] Create example claude_desktop_config.json
- [ ] Test integration with Claude Desktop
- [ ] Ensure human approval for sensitive sampling requests

## Implementation Plan

1. **Setup MCP Environment**
   - Install MCP Python SDK
   - Study MCP documentation and examples
   - Set up development environment for testing

2. **Design MCP Interface**
   - Map career agent workflows to MCP tools
   - Define tool parameters and return types
   - Design resource structure for data access

3. **Implement Core MCP Server with Sampling**

   ```python
   from mcp.server.fastmcp import FastMCP
   from mcp.types import SamplingRequest, Message
   
   mcp = FastMCP("career-agent")
   
   @mcp.tool()
   async def analyze_job(job_url: str, job_description: str = None) -> dict:
       """Analyze a job posting and provide tailored application recommendations"""
       # Use sampling to request LLM analysis
       sampling_request = SamplingRequest(
           messages=[
               Message(role="user", content=f"Analyze this job posting: {job_url}")
           ],
           model_preferences={"temperature": 0.7}
       )
       response = await mcp.sample(sampling_request)
       # Process response and return structured data
   
   @mcp.tool()
   async def generate_cv(job_url: str, template: str = "default") -> str:
       """Generate a tailored CV for a specific job"""
       # Use sampling for CV generation
       sampling_request = SamplingRequest(
           messages=[
               Message(role="system", content="You are a CV generation expert"),
               Message(role="user", content=f"Generate CV for job: {job_url}")
           ]
       )
       response = await mcp.sample(sampling_request)
       return response.content
   ```

4. **Implement MCP Tools**
   - `build_database`: Scan documents and build career database
   - `analyze_job`: Extract requirements and analyze fit
   - `research_company`: Gather company information
   - `generate_cv`: Create tailored CV
   - `generate_cover_letter`: Create cover letter
   - `get_recommendations`: Provide application strategy

5. **Add MCP Resources**
   - Career database YAML
   - Job analysis results
   - Generated documents
   - Company research findings

6. **Create MCP Prompts**
   - "Help me apply to this job"
   - "Update my career database"
   - "Analyze my fit for this role"
   - "Research this company"

7. **Integration Configuration**
   - Create example configurations for:
     - Claude Desktop
     - Cursor IDE
     - Custom AI agents
   - Document security considerations

## Technical Considerations

### MCP Sampling Architecture
- **All LLM operations must be routed through MCP sampling**
- Create a custom LLMWrapper that delegates to MCP client
- Replace all instances of `get_default_llm_wrapper()` with MCP-aware version
- Maintain prompt templates and conversation context
- Handle sampling request approvals and rejections

### MCP Architecture
- Server exposes tools, resources, and prompts
- Clients (Claude Desktop, IDEs) connect via JSON-RPC
- Stateless design for scalability
- Proper authentication and authorization

### Integration Points
- Create `MCPLLMWrapper` class that implements the same interface as `LLMWrapper`
- Route all node LLM calls through sampling requests
- Maintain backwards compatibility with existing nodes
- Async support for long-running operations
- Progress callbacks for UI updates

### Implementation Strategy
```python
class MCPLLMWrapper:
    """LLM wrapper that delegates to MCP client via sampling"""
    
    def __init__(self, mcp_context):
        self.mcp = mcp_context
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using MCP sampling"""
        sampling_request = SamplingRequest(
            messages=[Message(role="user", content=prompt)],
            model_preferences=kwargs
        )
        response = await self.mcp.sample(sampling_request)
        return response.content
    
    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """Generate structured response using MCP sampling"""
        # Include schema in prompt for structured output
        enhanced_prompt = f"{prompt}\n\nReturn response as JSON matching: {schema}"
        return await self.generate(enhanced_prompt)
```

### Security
- Validate all inputs
- Sanitize file paths
- Implement permission controls
- Audit logging for sensitive operations
- Request human approval for sensitive sampling operations

## Example Usage

Once implemented, users could:

1. In Claude Code:
   ```
   "I found this job posting [URL]. Can you help me apply?"
   -> Career agent analyzes job, generates tailored documents
   ```

2. In Cursor IDE:
   ```
   "Update my career database with this project I just completed"
   -> Scans code, extracts project details, updates database
   ```

3. In custom agent:
   ```python
   # Use career agent as sub-agent
   result = await mcp_client.call_tool(
       "analyze_job",
       {"job_url": "https://example.com/job"}
   )
   ```

## Benefits

### General Benefits

- **Seamless Integration**: Use career agent within existing workflows
- **Context Preservation**: No need to switch between tools
- **Composability**: Combine with other MCP servers
- **Standardization**: Follow industry-standard protocol
- **Extensibility**: Easy to add new capabilities

### Sampling Protocol Benefits

- **No API Keys Required**: Server doesn't need its own LLM configuration
- **Client Model Selection**: Uses whatever model the client is configured with
- **Cost Efficiency**: Billing handled by the client application
- **Consistent Experience**: Same model behavior as the host application
- **Security**: No need to manage or secure API credentials
- **Flexibility**: Works with any LLM provider the client supports

## References

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Building MCP Servers Tutorial](https://www.digitalocean.com/community/tutorials/mcp-server-python)
- [FastMCP Framework](https://modelcontextprotocol.io/quickstart/server)
