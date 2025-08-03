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

## Acceptance Criteria

- [ ] Research and understand MCP specification and best practices
- [ ] Install MCP Python SDK (`pip install mcp`)
- [ ] Create `mcp_server.py` that exposes career agent as MCP server
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
- [ ] Write documentation for MCP usage
- [ ] Create example claude_desktop_config.json
- [ ] Test integration with Claude Desktop

## Implementation Plan

1. **Setup MCP Environment**
   - Install MCP Python SDK
   - Study MCP documentation and examples
   - Set up development environment for testing

2. **Design MCP Interface**
   - Map career agent workflows to MCP tools
   - Define tool parameters and return types
   - Design resource structure for data access

3. **Implement Core MCP Server**
   ```python
   from mcp.server.fastmcp import FastMCP
   
   mcp = FastMCP("career-agent")
   
   @mcp.tool()
   def analyze_job(job_url: str, job_description: str = None) -> dict:
       """Analyze a job posting and provide tailored application recommendations"""
       # Implementation
   
   @mcp.tool()
   def generate_cv(job_url: str, template: str = "default") -> str:
       """Generate a tailored CV for a specific job"""
       # Implementation
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

### MCP Architecture
- Server exposes tools, resources, and prompts
- Clients (Claude Desktop, IDEs) connect via JSON-RPC
- Stateless design for scalability
- Proper authentication and authorization

### Integration Points
- Reuse existing nodes and flows
- Maintain backwards compatibility
- Async support for long-running operations
- Progress callbacks for UI updates

### Security
- Validate all inputs
- Sanitize file paths
- Implement permission controls
- Audit logging for sensitive operations

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

- **Seamless Integration**: Use career agent within existing workflows
- **Context Preservation**: No need to switch between tools
- **Composability**: Combine with other MCP servers
- **Standardization**: Follow industry-standard protocol
- **Extensibility**: Easy to add new capabilities

## References

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Building MCP Servers Tutorial](https://www.digitalocean.com/community/tutorials/mcp-server-python)
- [FastMCP Framework](https://modelcontextprotocol.io/quickstart/server)