"""
Async LLM wrapper for parallel API calls.

This module provides asynchronous interfaces to LLM APIs, enabling parallel
execution of multiple LLM calls for improved performance.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
import aiohttp
import yaml
from asyncio import Semaphore

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, rate: int = 10, per: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self._lock:
            current = time.monotonic()
            time_passed = current - self.last_check
            self.last_check = current
            
            # Replenish tokens
            self.allowance += time_passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            # Check if we can proceed
            if self.allowance < 1.0:
                # Need to wait
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0


class AsyncLLMWrapper:
    """Async LLM wrapper using aiohttp for parallel API calls."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "anthropic/claude-3-opus-20240229",
        app_name: Optional[str] = None,
        max_concurrent: int = 5,
        rate_limit: int = 10,
        rate_period: float = 1.0,
        timeout: float = 60.0
    ):
        """
        Initialize async LLM wrapper.
        
        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            base_url: OpenRouter API base URL
            default_model: Default model to use
            app_name: Optional app name for OpenRouter analytics
            max_concurrent: Maximum concurrent requests
            rate_limit: Maximum requests per rate_period
            rate_period: Rate limit period in seconds
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided or found in environment")
        
        self.base_url = base_url
        self.default_model = default_model
        self.app_name = app_name or "career-application-agent"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        # Rate limiting and concurrency control
        self.semaphore = Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(rate=rate_limit, per=rate_period)
        
        # Session will be created when needed
        self._session = None
        
        # Model aliases (same as sync wrapper)
        self.model_aliases = {
            "gpt-4": "openai/gpt-4",
            "gpt-4-turbo": "openai/gpt-4-turbo-preview",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
            "claude-3-opus": "anthropic/claude-3-opus-20240229",
            "claude-3-sonnet": "anthropic/claude-3-sonnet-20240229",
            "claude-3-haiku": "anthropic/claude-3-haiku-20240307",
            "gemini-pro": "google/gemini-pro",
            "mistral-large": "mistralai/mistral-large",
            "mixtral": "mistralai/mixtral-8x7b-instruct"
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": self.app_name,
                "X-Title": f"{self.app_name} (Async)"
            }
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout
            )
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _resolve_model(self, model: Optional[str] = None) -> str:
        """Resolve model name, handling aliases."""
        if not model:
            return self.default_model
        return self.model_aliases.get(model, model)
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Call LLM asynchronously.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            model: Model to use (optional, uses default if not specified)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters passed to API
            
        Returns:
            LLM response as string
        """
        await self._ensure_session()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        model_name = self._resolve_model(model)
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # Rate limiting and concurrency control
        async with self.semaphore:
            await self.rate_limiter.acquire()
            
            logger.info(f"Async calling {model_name} with prompt length: {len(prompt)}")
            
            try:
                async with self._session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    result = data["choices"][0]["message"]["content"]
                    logger.info(f"Received response length: {len(result)}")
                    
                    return result
                    
            except aiohttp.ClientError as e:
                logger.error(f"Async LLM API error: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in async LLM call: {e}")
                raise
    
    async def call_llm_batch(
        self,
        prompts: List[Tuple[str, Optional[str]]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> List[str]:
        """
        Call LLM for multiple prompts in parallel.
        
        Args:
            prompts: List of (prompt, system_prompt) tuples
            model: Model to use for all calls
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            **kwargs: Additional parameters
            
        Returns:
            List of responses in same order as prompts
        """
        tasks = [
            self.call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            for prompt, system_prompt in prompts
        ]
        
        return await asyncio.gather(*tasks)
    
    async def call_llm_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_format: str = "yaml",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 3000,
        max_retries: int = 3,
        **kwargs
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Call LLM expecting structured output (JSON or YAML).
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            output_format: Expected format ("json" or "yaml")
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            max_retries: Maximum parse retry attempts
            **kwargs: Additional parameters
            
        Returns:
            Parsed structured data
        """
        format_instruction = f"\nIMPORTANT: Your response must be ONLY valid {output_format.upper()} with no additional text or explanations."
        full_prompt = prompt + format_instruction
        
        for attempt in range(max_retries):
            try:
                response = await self.call_llm(
                    full_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
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
                if attempt == max_retries - 1:
                    raise
                
                # Add more explicit instructions for next attempt
                format_instruction = f"\nCRITICAL: Respond with ONLY valid {output_format.upper()} code. No explanations, no additional text, just the {output_format.upper()} structure."
                full_prompt = prompt + format_instruction
        
        raise ValueError(f"Failed to get valid {output_format} after {max_retries} attempts")


class CachedAsyncLLMWrapper(AsyncLLMWrapper):
    """Async LLM wrapper with caching support."""
    
    def __init__(self, *args, use_cache: bool = True, **kwargs):
        """
        Initialize cached async wrapper.
        
        Args:
            use_cache: Whether to enable caching
            *args, **kwargs: Passed to AsyncLLMWrapper
        """
        super().__init__(*args, **kwargs)
        self.use_cache = use_cache
        self._cache = None
        
        if use_cache:
            from .llm_cache import LLMCache, CacheBackend
            cache_backend = os.getenv("LLM_CACHE_BACKEND", "disk").lower()
            cache_dir = os.getenv("LLM_CACHE_DIR", ".llm_cache")
            cache_ttl = int(os.getenv("LLM_CACHE_TTL", str(3600 * 24 * 7)))
            
            self._cache = LLMCache(
                backend=CacheBackend(cache_backend),
                cache_dir=cache_dir,
                ttl=cache_ttl
            )
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> str:
        """Call LLM with caching support."""
        should_use_cache = self.use_cache if use_cache is None else use_cache
        
        if should_use_cache and self._cache:
            # Check cache
            cached = self._cache.get(
                prompt, system_prompt, model, temperature, max_tokens, **kwargs
            )
            if cached is not None:
                return cached
        
        # Make API call
        result = await super().call_llm(
            prompt, system_prompt, model, temperature, max_tokens, **kwargs
        )
        
        # Cache result
        if should_use_cache and self._cache:
            self._cache.set(
                result, prompt, system_prompt, model, temperature, max_tokens, **kwargs
            )
        
        return result


# Convenience function
async def get_async_llm_wrapper(**kwargs) -> AsyncLLMWrapper:
    """
    Get async LLM wrapper with optional caching.
    
    Args:
        **kwargs: Arguments for AsyncLLMWrapper
        
    Returns:
        AsyncLLMWrapper instance
    """
    use_cache = kwargs.pop("use_cache", None)
    if use_cache is None:
        use_cache = os.getenv("ENABLE_LLM_CACHE", "false").lower() == "true"
    
    if use_cache:
        return CachedAsyncLLMWrapper(use_cache=True, **kwargs)
    else:
        return AsyncLLMWrapper(**kwargs)