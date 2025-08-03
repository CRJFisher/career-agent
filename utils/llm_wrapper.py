"""
LLM utility wrapper using OpenRouter for unified API access.

OpenRouter provides access to multiple LLM providers through a single API key
using the OpenAI format. This simplifies our implementation significantly.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from openai import OpenAI
import yaml

logger = logging.getLogger(__name__)


class LLMWrapper:
    """LLM wrapper using OpenRouter for unified access to multiple providers."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "anthropic/claude-3-opus-20240229",
        app_name: Optional[str] = None
    ):
        """
        Initialize LLM wrapper with OpenRouter.
        
        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            base_url: OpenRouter API base URL
            default_model: Default model to use
            app_name: Optional app name for OpenRouter analytics
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided or found in environment")
        
        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            base_url=base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": app_name or "career-application-agent",
                "X-Title": app_name or "Career Application Agent"
            } if app_name else None
        )
        
        self.default_model = default_model
        
        # Common model mappings for convenience
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
    
    def _resolve_model(self, model: Optional[str] = None) -> str:
        """Resolve model name, handling aliases."""
        if not model:
            return self.default_model
        
        # Check if it's an alias
        if model in self.model_aliases:
            return self.model_aliases[model]
        
        # Return as-is if not an alias
        return model
    
    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Call LLM with unified interface.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            model: Model to use (optional, uses default if not specified)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters passed to OpenAI API
            
        Returns:
            LLM response as string
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        model_name = self._resolve_model(model)
        logger.info(f"Calling {model_name} with prompt length: {len(prompt)}")
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            result = response.choices[0].message.content
            logger.info(f"Received response length: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            raise
    
    def call_llm_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_format: str = "yaml",
        model: Optional[str] = None,
        temperature: float = 0.3,  # Lower default for structured output
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
            temperature: Sampling temperature (lower for more consistent output)
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
                response = self.call_llm(
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
    
    def call_llm_sync(self, prompt: str, **kwargs) -> str:
        """
        Synchronous version of call_llm.
        Since we're using the OpenAI client which is already synchronous,
        this is just an alias for call_llm.
        """
        return self.call_llm(prompt, **kwargs)
    
    def call_llm_structured_sync(self, prompt: str, **kwargs) -> Union[Dict[str, Any], List[Any]]:
        """
        Synchronous version of call_llm_structured.
        Since we're using the OpenAI client which is already synchronous,
        this is just an alias for call_llm_structured.
        """
        return self.call_llm_structured(prompt, **kwargs)
    
    def list_models(self) -> List[str]:
        """
        List available models through OpenRouter.
        
        Returns:
            List of available model IDs
        """
        try:
            # OpenRouter doesn't support the models endpoint in the same way
            # Return common models instead
            return list(self.model_aliases.values()) + [
                "meta-llama/llama-3-70b-instruct",
                "meta-llama/llama-3-8b-instruct",
                "nous-hermes-2-mixtral-8x7b-dpo",
                "databricks/dbrx-instruct",
                "cohere/command-r-plus",
                "deepseek/deepseek-chat"
            ]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


# Global instance for convenience
_default_wrapper = None


def get_default_llm_wrapper(use_cache: bool = None, **kwargs) -> LLMWrapper:
    """
    Get or create default LLM wrapper instance.
    
    Args:
        use_cache: Whether to enable caching (defaults to ENABLE_LLM_CACHE env var)
        **kwargs: Arguments passed to LLMWrapper constructor
        
    Returns:
        LLMWrapper instance (possibly wrapped with caching)
    """
    global _default_wrapper
    
    if _default_wrapper is None:
        base_wrapper = LLMWrapper(**kwargs)
        
        # Check if caching should be enabled
        if use_cache is None:
            use_cache = os.getenv("ENABLE_LLM_CACHE", "false").lower() == "true"
        
        if use_cache:
            from .llm_cache import CachedLLMWrapper, CacheBackend
            
            # Get cache configuration from environment
            cache_backend = os.getenv("LLM_CACHE_BACKEND", "disk").lower()
            cache_dir = os.getenv("LLM_CACHE_DIR", ".llm_cache")
            cache_ttl = int(os.getenv("LLM_CACHE_TTL", str(3600 * 24 * 7)))  # 1 week default
            
            _default_wrapper = CachedLLMWrapper(
                base_wrapper=base_wrapper,
                cache_backend=CacheBackend(cache_backend),
                cache_dir=cache_dir,
                ttl=cache_ttl
            )
            logger.info(f"LLM caching enabled with {cache_backend} backend")
        else:
            _default_wrapper = base_wrapper
    
    return _default_wrapper


# Example usage
if __name__ == "__main__":
    # Example: Using the wrapper
    wrapper = get_default_llm_wrapper()
    
    # Simple completion
    response = wrapper.call_llm(
        "What is the capital of France?",
        model="claude-3-haiku"  # Using alias
    )
    print(f"Response: {response}")
    
    # Structured output
    structured = wrapper.call_llm_structured(
        "List 3 programming languages with their main use cases",
        output_format="yaml"
    )
    print(f"Structured response: {structured}")