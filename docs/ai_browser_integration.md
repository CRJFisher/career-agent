# AI Browser Integration Guide

**Date**: 2025-08-03  
**Version**: 1.0  
**Status**: Phase 2 Implementation Complete

## Overview

The Career Application Agent now includes AI-powered browser functionality for advanced web interactions. This integration is based on the research documented in [ai_browser_tools_evaluation.md](ai_browser_tools_evaluation.md) and implements the recommended hybrid approach using LangChain Browser Tools with custom extensions.

## Architecture

### Components

1. **AIBrowser** (`utils/ai_browser.py`)
   - Main browser automation class
   - Wraps LangChain's PlayWrightBrowserToolkit
   - Provides custom tools for job applications
   - Async-first design for performance

2. **AISimpleScraper** (`utils/ai_browser.py`)
   - Lightweight alternative for content extraction
   - No browser overhead for simple scraping
   - Uses aiohttp + BeautifulSoup + LLM

3. **BrowserActionNode** (`nodes.py`)
   - PocketFlow node for browser interactions
   - Supports multiple action types
   - Handles async operations seamlessly
   - Integrates with existing workflow

## Installation

### Prerequisites

```bash
# Install required dependencies
pip install langchain-community playwright beautifulsoup4 aiohttp

# Install Playwright browsers
playwright install chromium
```

### Optional Dependencies

For full functionality, you may also want:

```bash
# For stealth mode (avoiding detection)
pip install playwright-stealth

# For better HTML parsing
pip install lxml
```

## Usage

### 1. Job Listing Extraction

Extract job listings from a job board:

```python
# In your flow or node
shared["browser_action"] = {
    "action_type": "extract_jobs",
    "url": "https://www.indeed.com/jobs?q=software+engineer&l=remote"
}
```

The node will:
- Navigate to the job board
- Identify job listing containers
- Extract structured data (title, company, location, link)
- Store results in `shared["extracted_job_listings"]`

### 2. Job Application Form Filling

Fill out a job application form:

```python
shared["browser_action"] = {
    "action_type": "fill_application",
    "url": "https://company.com/careers/apply/12345",
    "form_data": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "resume": "/path/to/resume.pdf",
        "cover_letter": "Generated cover letter text...",
        "years_experience": "5-7"
    },
    "submit": False,  # Set to True to auto-submit
    "submit_selector": 'button[type="submit"]'  # Optional custom selector
}
```

The node will:
- Navigate to the application page
- Intelligently find form fields by name, placeholder, or label
- Fill in the provided data
- Optionally submit the form
- Return status in `shared["application_status"]`

### 3. Dynamic Content Extraction

Extract data from pages with JavaScript-rendered content:

```python
shared["browser_action"] = {
    "action_type": "navigate_and_extract",
    "url": "https://company.com/about",
    "instruction": "Extract company values, culture description, and team size"
}
```

The node will:
- Navigate and wait for content to load
- Use LLM to understand the extraction request
- Extract structured data based on instructions
- Store in `shared["extracted_data"]`

### 4. Simple Content Extraction

For static pages, use the lightweight scraper:

```python
shared["browser_action"] = {
    "action_type": "simple_extract",
    "url": "https://company.com/team",
    "prompt": "Extract all team member names and their roles"
}
```

This is faster and more resource-efficient for simple extractions.

## Integration with Company Research Flow

The `DecideActionNode` has been updated to support browser actions:

```yaml
# Example decision from DecideActionNode
thinking: |
  Found company careers page but it uses dynamic loading.
  Need to use browser action to extract job listings.
  
action:
  type: browser_action
  parameters:
    action_type: extract_jobs
    url: https://company.com/careers
```

### Flow Example

```python
from pocketflow import Flow
from nodes import (
    DecideActionNode, 
    WebSearchNode, 
    ReadContentNode,
    BrowserActionNode,
    SynthesizeNode
)

# Create research flow with browser capabilities
research_flow = Flow(start=DecideActionNode())

# Connect nodes
decide = DecideActionNode()
search = WebSearchNode()
read = ReadContentNode()
browser = BrowserActionNode()
synthesize = SynthesizeNode()

# Define transitions
flow = (
    decide 
    >> {
        "web_search": search,
        "read_content": read,
        "browser_action": browser,
        "synthesize": synthesize
    }
)

# All nodes loop back to decide except synthesize
search >> decide
read >> decide
browser >> {
    "browser_success": decide,
    "browser_failed": decide
}
synthesize >> "complete"
```

## Custom Tool Development

### Adding New Browser Tools

To add custom browser tools to AIBrowser:

```python
def _setup_custom_tools(self):
    """Set up both default and custom tools."""
    self.tools = self.toolkit.get_tools()
    
    # Add your custom tool
    self.tools.append(Tool(
        name="handle_modal",
        func=self._handle_modal,
        description="Handle modal dialogs (close, accept, extract content)"
    ))

async def _handle_modal(self, action: str = "close") -> str:
    """Handle modal dialogs."""
    try:
        # Wait for modal
        modal = await self.page.wait_for_selector('.modal', timeout=5000)
        
        if action == "close":
            close_button = await modal.query_selector('.close-button')
            await close_button.click()
            return "Modal closed"
        elif action == "accept":
            accept_button = await modal.query_selector('.accept-button')
            await accept_button.click()
            return "Modal accepted"
        elif action == "extract":
            content = await modal.text_content()
            return f"Modal content: {content}"
    except Exception as e:
        return f"No modal found or error: {str(e)}"
```

### Adding New Action Types

To add new action types to BrowserActionNode:

```python
# In _exec_async method
elif action_type == "your_new_action":
    return await self._your_new_action(action_config)

# Add the implementation
async def _your_new_action(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Implement your custom action."""
    # Your implementation here
    return {
        "success": True,
        "result": "Your result"
    }
```

## Best Practices

### 1. Resource Management

- The browser instance is kept alive during node execution
- Proper cleanup happens automatically via `__del__`
- For long-running flows, consider periodic browser restarts

### 2. Error Handling

- All browser actions are wrapped in try-except blocks
- Failures return structured error responses
- The flow can decide how to handle failures

### 3. Performance Optimization

- Use `simple_extract` for static content
- Batch similar operations when possible
- Configure appropriate timeouts for your use case

### 4. Security Considerations

- Never auto-submit forms in production without user consent
- Validate URLs before navigation
- Be mindful of rate limiting on target sites
- Respect robots.txt and terms of service

## Troubleshooting

### Common Issues

1. **Import Error**: "BrowserActionNode requires AI browser dependencies"
   ```bash
   pip install langchain-community playwright
   playwright install chromium
   ```

2. **Browser Launch Failure**: "Browser failed to start"
   - Check Playwright installation: `playwright install`
   - Verify system dependencies for headless Chrome
   - Try with `headless=False` for debugging

3. **Timeout Errors**: Elements not found
   - Increase wait times in browser configuration
   - Check if site uses anti-bot measures
   - Verify CSS selectors are correct

4. **Form Filling Failures**: Fields not found
   - Log the page HTML to verify field names
   - Try different selector strategies
   - Check if fields are in iframes

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging

# Enable debug logging
logging.getLogger('utils.ai_browser').setLevel(logging.DEBUG)
logging.getLogger('nodes').setLevel(logging.DEBUG)

# Run browser with headless=False to see what's happening
browser = AIBrowser(llm_wrapper, headless=False)
```

## Future Enhancements

Based on the research document, potential future enhancements include:

1. **Stealth Mode**: Implement anti-detection measures
2. **Session Management**: Handle login states across requests
3. **Parallel Browsing**: Multiple browser instances for speed
4. **Visual AI**: Screenshot analysis for complex interactions
5. **Proxy Support**: Route through different IPs
6. **Cookie Management**: Save and restore sessions

## API Reference

### AIBrowser

```python
class AIBrowser:
    def __init__(self, llm_wrapper: LLMWrapper, headless: bool = True)
    async def setup()
    async def navigate_and_extract(url: str, instruction: str) -> Dict[str, Any]
    async def close()
```

### BrowserActionNode

```python
class BrowserActionNode(Node):
    # Inherits from PocketFlow Node
    # Supports action_types: 
    # - extract_jobs
    # - fill_application  
    # - navigate_and_extract
    # - simple_extract
```

### Action Configuration Schema

```yaml
# Extract Jobs
browser_action:
  action_type: extract_jobs
  url: <job_board_url>

# Fill Application  
browser_action:
  action_type: fill_application
  url: <application_url>
  form_data:
    <field_name>: <value>
  submit: <true|false>
  submit_selector: <optional_css_selector>

# Navigate and Extract
browser_action:
  action_type: navigate_and_extract
  url: <target_url>
  instruction: <natural_language_instruction>

# Simple Extract
browser_action:
  action_type: simple_extract
  url: <target_url>
  prompt: <extraction_prompt>
```

## Conclusion

The AI browser integration provides powerful capabilities for interacting with modern web applications. By combining LangChain's browser tools with custom extensions, we've created a flexible system that can handle the complex requirements of job application automation while remaining maintainable and extensible.