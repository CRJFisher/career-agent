"""AI-powered browser for complex web interactions.

This module provides browser automation capabilities using LangChain's PlayWrightBrowserToolkit
with custom extensions for job application specific tasks.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from langchain.tools.playwright import PlaywrightBrowserToolkit
    from langchain.tools import Tool
    from langchain.agents import AgentType, initialize_agent
    from playwright.async_api import async_playwright, Browser, Page
except ImportError as e:
    raise ImportError(
        "AI browser functionality requires additional dependencies. "
        "Install with: pip install langchain-community playwright"
    ) from e

from .llm_wrapper import LLMWrapper

logger = logging.getLogger(__name__)


class AIBrowser:
    """AI-powered browser for complex web interactions.
    
    This class wraps LangChain's PlayWrightBrowserToolkit and adds custom tools
    specifically designed for job application workflows.
    """
    
    def __init__(self, llm_wrapper: LLMWrapper, headless: bool = True):
        """Initialize the AI browser.
        
        Args:
            llm_wrapper: The LLM wrapper instance to use
            headless: Whether to run browser in headless mode
        """
        self.llm = llm_wrapper
        self.headless = headless
        self.browser = None
        self.page = None
        self.toolkit = None
        self.tools = []
        self._setup_complete = False
        
    async def setup(self):
        """Set up the browser and tools."""
        if self._setup_complete:
            return
            
        # Initialize Playwright browser
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        
        # Create toolkit
        self.toolkit = PlaywrightBrowserToolkit.from_browser(
            sync_browser=None,  # We'll manage async browser ourselves
            async_browser=self.browser
        )
        
        # Get default tools and add custom ones
        self._setup_tools()
        self._setup_complete = True
        
    def _setup_tools(self):
        """Set up both default and custom tools."""
        # Get default LangChain browser tools
        self.tools = self.toolkit.get_tools()
        
        # Add our custom tools
        custom_tools = [
            Tool(
                name="fill_job_application",
                func=self._fill_job_form,
                description=(
                    "Intelligently fill out a job application form. "
                    "Provide the form data as a dictionary with field names and values."
                )
            ),
            Tool(
                name="extract_job_listings",
                func=self._extract_job_listings,
                description=(
                    "Extract job listings from a job board page. "
                    "Returns structured data with title, company, location, and apply link."
                )
            ),
            Tool(
                name="wait_for_element",
                func=self._wait_for_element,
                description=(
                    "Wait for a specific element to appear on the page. "
                    "Provide a CSS selector to wait for."
                )
            ),
            Tool(
                name="screenshot",
                func=self._take_screenshot,
                description=(
                    "Take a screenshot of the current page. "
                    "Optionally provide a filename, otherwise uses timestamp."
                )
            ),
            Tool(
                name="handle_pagination",
                func=self._handle_pagination,
                description=(
                    "Navigate through paginated content. "
                    "Provide the CSS selector for the 'next' button."
                )
            )
        ]
        
        self.tools.extend(custom_tools)
        
    async def navigate_and_extract(self, url: str, instruction: str) -> Dict[str, Any]:
        """Navigate to URL and extract data based on instruction.
        
        Args:
            url: The URL to navigate to
            instruction: Natural language instruction for what to extract
            
        Returns:
            Extracted data as a dictionary
        """
        if not self._setup_complete:
            await self.setup()
            
        try:
            # Create a new page for this operation
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle")
            
            # Get page content
            content = await page.content()
            
            # Use LLM to determine extraction strategy
            extraction_prompt = f"""
            Given this webpage content (truncated):
            {content[:3000]}...
            
            User wants to: {instruction}
            
            Provide a structured extraction plan with:
            1. CSS selectors to target
            2. Data to extract from each element
            3. How to structure the output
            
            Return as JSON.
            """
            
            plan = await self.llm.call_llm(
                extraction_prompt,
                response_format="json",
                max_tokens=1000
            )
            
            # Execute extraction based on plan
            # This is simplified - in reality would parse the plan and execute
            result = await self._execute_extraction_plan(page, plan)
            
            await page.close()
            return result
            
        except Exception as e:
            logger.error(f"Error in navigate_and_extract: {e}")
            raise
            
    async def _execute_extraction_plan(self, page: Page, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an extraction plan on a page."""
        # This is a simplified implementation
        # In reality, this would parse the LLM's plan and execute it
        return {"status": "extracted", "data": plan}
        
    async def _fill_job_form(self, form_data: Dict[str, str]) -> str:
        """Fill out a job application form intelligently.
        
        Args:
            form_data: Dictionary mapping field names to values
            
        Returns:
            Status message
        """
        if not self.page:
            return "Error: No active page. Navigate to a form first."
            
        try:
            filled_fields = []
            
            for field_name, value in form_data.items():
                # Try multiple strategies to find the field
                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[placeholder*="{field_name}" i]',
                    f'label:has-text("{field_name}") + input',
                    f'textarea[name="{field_name}"]',
                    f'select[name="{field_name}"]'
                ]
                
                field_found = False
                for selector in selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=1000)
                        if element:
                            # Determine field type and fill appropriately
                            tag_name = await element.evaluate("el => el.tagName")
                            
                            if tag_name == "SELECT":
                                await element.select_option(value)
                            else:
                                await element.fill(value)
                                
                            filled_fields.append(field_name)
                            field_found = True
                            break
                    except:
                        continue
                        
                if not field_found:
                    logger.warning(f"Could not find field: {field_name}")
                    
            return f"Successfully filled {len(filled_fields)} fields: {', '.join(filled_fields)}"
            
        except Exception as e:
            return f"Error filling form: {str(e)}"
            
    async def _extract_job_listings(self, container_selector: str = None) -> List[Dict[str, str]]:
        """Extract job listings from current page.
        
        Args:
            container_selector: Optional CSS selector for job listing container
            
        Returns:
            List of job listings with structured data
        """
        if not self.page:
            return []
            
        try:
            # If no container specified, try to detect it
            if not container_selector:
                # Common patterns for job listing containers
                possible_selectors = [
                    '[data-testid*="job"]',
                    '.job-listing',
                    '.job-card',
                    '[class*="JobCard"]',
                    'article',
                    '.result'
                ]
                
                for selector in possible_selectors:
                    elements = await self.page.query_selector_all(selector)
                    if len(elements) > 2:  # Found multiple, likely job listings
                        container_selector = selector
                        break
                        
            if not container_selector:
                return []
                
            # Extract data from each listing
            listings = await self.page.evaluate(f"""
                () => {{
                    const containers = document.querySelectorAll('{container_selector}');
                    return Array.from(containers).map(container => {{
                        // Try to extract common job listing fields
                        const getTextContent = (selectors) => {{
                            for (const selector of selectors) {{
                                const el = container.querySelector(selector);
                                if (el) return el.textContent.trim();
                            }}
                            return '';
                        }};
                        
                        return {{
                            title: getTextContent(['h2', 'h3', '[class*="title"]', 'a']),
                            company: getTextContent(['[class*="company"]', '[data-testid*="company"]']),
                            location: getTextContent(['[class*="location"]', '[data-testid*="location"]']),
                            salary: getTextContent(['[class*="salary"]', '[class*="compensation"]']),
                            link: container.querySelector('a')?.href || ''
                        }};
                    }}).filter(job => job.title);  // Filter out empty results
                }}
            """)
            
            return listings
            
        except Exception as e:
            logger.error(f"Error extracting job listings: {e}")
            return []
            
    async def _wait_for_element(self, selector: str, timeout: int = 30000) -> str:
        """Wait for an element to appear on the page.
        
        Args:
            selector: CSS selector to wait for
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            Status message
        """
        if not self.page:
            return "Error: No active page"
            
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return f"Element found: {selector}"
        except Exception as e:
            return f"Timeout waiting for element: {selector}"
            
    async def _take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot of the current page.
        
        Args:
            filename: Optional filename for the screenshot
            
        Returns:
            Path to the saved screenshot
        """
        if not self.page:
            return "Error: No active page"
            
        try:
            if not filename:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                
            # Ensure screenshots directory exists
            screenshot_dir = Path("screenshots")
            screenshot_dir.mkdir(exist_ok=True)
            
            filepath = screenshot_dir / filename
            await self.page.screenshot(path=str(filepath))
            
            return str(filepath)
            
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
            
    async def _handle_pagination(self, next_button_selector: str, max_pages: int = 5) -> str:
        """Navigate through paginated content.
        
        Args:
            next_button_selector: CSS selector for the next button
            max_pages: Maximum number of pages to navigate
            
        Returns:
            Status message
        """
        if not self.page:
            return "Error: No active page"
            
        pages_navigated = 0
        
        try:
            while pages_navigated < max_pages:
                # Check if next button exists and is enabled
                next_button = await self.page.query_selector(next_button_selector)
                
                if not next_button:
                    break
                    
                # Check if button is disabled
                is_disabled = await next_button.evaluate("el => el.disabled || el.getAttribute('aria-disabled') === 'true'")
                
                if is_disabled:
                    break
                    
                # Click next button
                await next_button.click()
                
                # Wait for page to load
                await self.page.wait_for_load_state("networkidle")
                
                pages_navigated += 1
                await asyncio.sleep(1)  # Be polite to the server
                
            return f"Navigated through {pages_navigated} pages"
            
        except Exception as e:
            return f"Error during pagination: {str(e)}"
            
    async def close(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._setup_complete = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class AISimpleScraper:
    """Simplified AI scraper for content extraction without interaction.
    
    This is a lightweight alternative when you only need to extract data
    and don't need form filling or complex navigation.
    """
    
    def __init__(self, llm_wrapper: LLMWrapper):
        """Initialize the simple scraper.
        
        Args:
            llm_wrapper: The LLM wrapper instance to use
        """
        self.llm = llm_wrapper
        
    async def extract(self, url: str, prompt: str) -> Dict[str, Any]:
        """Extract structured data from a URL using natural language prompt.
        
        Args:
            url: The URL to scrape
            prompt: Natural language description of what to extract
            
        Returns:
            Extracted data as a dictionary
        """
        try:
            # For simple extraction, we can use requests + BeautifulSoup
            # This is much lighter than full browser automation
            import aiohttp
            from bs4 import BeautifulSoup
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Use LLM to extract structured data
            extraction_prompt = f"""
            Extract the following information from this webpage content:
            {prompt}
            
            Webpage content:
            {text[:5000]}...
            
            Return the extracted information as JSON.
            """
            
            result = await self.llm.call_llm(
                extraction_prompt,
                response_format="json",
                max_tokens=1500
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in simple extraction: {e}")
            return {"error": str(e)}