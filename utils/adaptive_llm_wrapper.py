"""
Adaptive LLM Wrapper that supports both MCP sampling and direct API calls.

This wrapper automatically adapts between two modes:
1. MCP Sampling Mode: When running as an MCP server, delegates LLM calls to the client
2. Standalone Mode: When running independently, uses direct API calls with tokens
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
import asyncio
from datetime import datetime

from .llm_wrapper import LLMWrapper, get_default_llm_wrapper

logger = logging.getLogger(__name__)


class AdaptiveLLMWrapper:
    """
    LLM wrapper that adapts between MCP sampling and direct API calls.
    
    This allows the career agent to work in two modes:
    - As an MCP server: Routes LLM calls through client sampling (no API keys needed)
    - Standalone: Uses traditional API calls with authentication
    """
    
    def __init__(self, mcp_context=None):
        """
        Initialize the adaptive wrapper.
        
        Args:
            mcp_context: FastMCP Context object if running as MCP server, None otherwise
        """
        self.mcp_context = mcp_context
        self.standalone_wrapper = None
        self.mode = "mcp" if mcp_context else "standalone"
        
        if not mcp_context:
            # Standalone mode - use traditional wrapper
            try:
                self.standalone_wrapper = get_default_llm_wrapper()
                logger.info("Initialized in standalone mode with API keys")
            except Exception as e:
                logger.error(f"Failed to initialize standalone wrapper: {e}")
                raise
        else:
            logger.info("Initialized in MCP sampling mode")
    
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """
        Generate response using appropriate method (async).
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text response
        """
        if self.mcp_context:
            return await self._mcp_generate(prompt, **kwargs)
        else:
            # Convert sync to async if needed
            if hasattr(self.standalone_wrapper, 'generate_async'):
                return await self.standalone_wrapper.generate_async(prompt, **kwargs)
            else:
                # Run sync method in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, 
                    self.standalone_wrapper.call_llm_sync, 
                    prompt,
                    kwargs.get('max_tokens', 2000),
                    kwargs.get('temperature', 0.7)
                )
    
    def call_llm_sync(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """
        Synchronous generate method for compatibility with existing nodes.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Generated text response
        """
        if self.mcp_context:
            # Run async method in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an async context
                    task = asyncio.create_task(
                        self._mcp_generate(prompt, max_tokens=max_tokens, temperature=temperature)
                    )
                    # This is a workaround - in practice, nodes should use async
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, 
                            self._mcp_generate(prompt, max_tokens=max_tokens, temperature=temperature)
                        )
                        return future.result()
                else:
                    return asyncio.run(
                        self._mcp_generate(prompt, max_tokens=max_tokens, temperature=temperature)
                    )
            except Exception as e:
                logger.error(f"Error in sync MCP call: {e}")
                raise
        else:
            return self.standalone_wrapper.call_llm_sync(prompt, max_tokens, temperature)
    
    async def _mcp_generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using MCP sampling.
        
        Args:
            prompt: The prompt to send via sampling
            **kwargs: Additional parameters for sampling
            
        Returns:
            Generated text from client's LLM
        """
        try:
            # Log the sampling request
            logger.debug(f"MCP sampling request: {prompt[:100]}...")
            
            # Use FastMCP's context.sample() method
            response = await self.mcp_context.sample(
                prompt,
                max_tokens=kwargs.get('max_tokens', 2000),
                temperature=kwargs.get('temperature', 0.7),
                # Include any system context if provided
                system=kwargs.get('system_prompt')
            )
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif isinstance(response, dict) and 'text' in response:
                return response['text']
            elif isinstance(response, str):
                return response
            else:
                logger.error(f"Unexpected response type from sampling: {type(response)}")
                return str(response)
                
        except Exception as e:
            logger.error(f"MCP sampling error: {e}")
            # Provide helpful error message
            error_msg = f"MCP sampling failed: {str(e)}"
            if "denied" in str(e).lower():
                error_msg += "\n\nThe sampling request was denied by the user."
            raise RuntimeError(error_msg) from e
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate structured response (JSON) using appropriate method.
        
        Args:
            prompt: The prompt to send to the LLM
            schema: Expected JSON schema for the response
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        if self.mcp_context:
            # For MCP, include schema in prompt
            enhanced_prompt = f"""{prompt}

Please respond with valid JSON that matches this schema:
{json.dumps(schema, indent=2)}

Ensure your response is properly formatted JSON that can be parsed."""
            
            response = await self._mcp_generate(enhanced_prompt, **kwargs)
            
            # Try to extract JSON from response
            try:
                # Look for JSON in code blocks
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_text = response[json_start:json_end].strip()
                elif "```" in response:
                    json_start = response.find("```") + 3
                    json_end = response.find("```", json_start)
                    json_text = response[json_start:json_end].strip()
                else:
                    json_text = response
                
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from MCP response: {e}")
                logger.debug(f"Response was: {response}")
                # Return a default structure based on schema
                return self._create_default_from_schema(schema)
        else:
            # Use standalone wrapper's structured generation if available
            if hasattr(self.standalone_wrapper, 'generate_structured'):
                return await self.standalone_wrapper.generate_structured(prompt, schema, **kwargs)
            else:
                # Fallback to regular generation with JSON parsing
                response = await self.generate_async(prompt, **kwargs)
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return self._create_default_from_schema(schema)
    
    def _create_default_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create a default response based on schema."""
        # This is a simplified version - in production would be more sophisticated
        result = {}
        if "properties" in schema:
            for key, prop in schema["properties"].items():
                if prop.get("type") == "string":
                    result[key] = ""
                elif prop.get("type") == "number":
                    result[key] = 0
                elif prop.get("type") == "array":
                    result[key] = []
                elif prop.get("type") == "object":
                    result[key] = {}
                elif prop.get("type") == "boolean":
                    result[key] = False
        return result
    
    def get_mode(self) -> str:
        """Get the current operating mode."""
        return self.mode
    
    def is_mcp_mode(self) -> bool:
        """Check if running in MCP mode."""
        return self.mcp_context is not None
    
    def is_standalone_mode(self) -> bool:
        """Check if running in standalone mode."""
        return self.mcp_context is None
    
    # Compatibility methods to match LLMWrapper interface
    
    def call_llm(self, *args, **kwargs):
        """Alias for call_llm_sync for compatibility."""
        return self.call_llm_sync(*args, **kwargs)
    
    async def acall_llm(self, *args, **kwargs):
        """Alias for generate_async for compatibility."""
        return await self.generate_async(*args, **kwargs)
    
    def generate(self, *args, **kwargs):
        """Alias for call_llm_sync for compatibility."""
        return self.call_llm_sync(*args, **kwargs)
    
    # Batch operations (for parallel processing)
    
    async def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate responses for multiple prompts.
        
        In MCP mode, this will result in multiple sampling requests.
        In standalone mode, may use parallel API calls if supported.
        """
        if self.mcp_context:
            # MCP mode - serialize requests (user needs to approve each)
            results = []
            for i, prompt in enumerate(prompts):
                try:
                    await self.mcp_context.info(f"Processing prompt {i+1}/{len(prompts)}")
                    result = await self._mcp_generate(prompt, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing prompt {i}: {e}")
                    results.append(f"Error: {str(e)}")
            return results
        else:
            # Standalone mode - use parallel processing if available
            if hasattr(self.standalone_wrapper, 'generate_batch'):
                return await self.standalone_wrapper.generate_batch(prompts, **kwargs)
            else:
                # Fallback to sequential processing
                tasks = [self.generate_async(prompt, **kwargs) for prompt in prompts]
                return await asyncio.gather(*tasks)


# Factory function for backward compatibility
def get_adaptive_llm_wrapper(mcp_context=None) -> AdaptiveLLMWrapper:
    """
    Factory function to create an adaptive LLM wrapper.
    
    Args:
        mcp_context: FastMCP Context if running as MCP server
        
    Returns:
        AdaptiveLLMWrapper instance
    """
    return AdaptiveLLMWrapper(mcp_context)