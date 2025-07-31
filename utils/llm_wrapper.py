"""
LLM utility wrapper for unified API interactions.

Provides a consistent interface for LLM calls across different providers.
Handles retries, rate limiting, and error management.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import openai
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make an LLM API call."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided or found in environment")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.model = model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call OpenAI API with retry logic."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic API provider implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided or found in environment")
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.model = model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def call(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Call Anthropic API with retry logic."""
        try:
            # Convert OpenAI format to Anthropic format
            system_message = None
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            response = await self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=user_messages,
                max_tokens=kwargs.get("max_tokens", 2000),
                temperature=kwargs.get("temperature", 0.7),
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class LLMWrapper:
    """Unified LLM wrapper supporting multiple providers."""
    
    def __init__(self, provider: str = "openai", **kwargs):
        """
        Initialize LLM wrapper with specified provider.
        
        Args:
            provider: Provider name ("openai" or "anthropic")
            **kwargs: Provider-specific configuration
        """
        self.provider_name = provider
        
        if provider == "openai":
            self.provider = OpenAIProvider(**kwargs)
        elif provider == "anthropic":
            self.provider = AnthropicProvider(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Call LLM with unified interface.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLM response as string
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        logger.info(f"Calling {self.provider_name} with prompt length: {len(prompt)}")
        
        response = await self.provider.call(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        logger.info(f"Received response length: {len(response)}")
        
        return response
    
    async def call_llm_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_format: str = "yaml",
        retry_on_parse_error: bool = True,
        max_retries: int = 3,
        **kwargs
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Call LLM expecting structured output (JSON or YAML).
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            output_format: Expected format ("json" or "yaml")
            retry_on_parse_error: Whether to retry on parse errors
            max_retries: Maximum parse retry attempts
            **kwargs: Additional parameters
            
        Returns:
            Parsed structured data
        """
        import yaml
        
        format_instruction = f"\nPlease respond with valid {output_format.upper()} only, no additional text."
        full_prompt = prompt + format_instruction
        
        for attempt in range(max_retries):
            try:
                response = await self.call_llm(
                    full_prompt,
                    system_prompt=system_prompt,
                    **kwargs
                )
                
                # Try to extract structured content
                if output_format == "yaml":
                    # Find YAML block if wrapped in markdown
                    if "```yaml" in response:
                        start = response.find("```yaml") + 7
                        end = response.find("```", start)
                        if end > start:
                            response = response[start:end].strip()
                    elif "```" in response:
                        # Generic code block
                        start = response.find("```") + 3
                        if response[start:start+1] == "\n":
                            start += 1
                        end = response.find("```", start)
                        if end > start:
                            response = response[start:end].strip()
                    
                    return yaml.safe_load(response)
                    
                elif output_format == "json":
                    # Find JSON block if wrapped in markdown
                    if "```json" in response:
                        start = response.find("```json") + 7
                        end = response.find("```", start)
                        if end > start:
                            response = response[start:end].strip()
                    elif "```" in response:
                        # Generic code block
                        start = response.find("```") + 3
                        if response[start:start+1] == "\n":
                            start += 1
                        end = response.find("```", start)
                        if end > start:
                            response = response[start:end].strip()
                    
                    return json.loads(response)
                    
            except (yaml.YAMLError, json.JSONDecodeError) as e:
                logger.warning(f"Parse error on attempt {attempt + 1}: {e}")
                if not retry_on_parse_error or attempt == max_retries - 1:
                    raise
                
                # Add more explicit instructions for next attempt
                format_instruction = f"\nIMPORTANT: Respond ONLY with valid {output_format.upper()}, no explanations or additional text. The response must be parseable."
                full_prompt = prompt + format_instruction
        
        raise ValueError(f"Failed to get valid {output_format} after {max_retries} attempts")


# Global instance for convenience
_default_wrapper = None


def get_default_llm_wrapper(provider: Optional[str] = None, **kwargs) -> LLMWrapper:
    """Get or create default LLM wrapper instance."""
    global _default_wrapper
    
    if _default_wrapper is None or provider is not None:
        provider = provider or os.getenv("LLM_PROVIDER", "openai")
        _default_wrapper = LLMWrapper(provider, **kwargs)
    
    return _default_wrapper