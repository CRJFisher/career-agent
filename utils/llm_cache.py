"""
LLM caching functionality for development and testing.

This module provides caching capabilities for LLM responses to:
- Reduce API costs during development
- Speed up testing and development iterations
- Enable offline development with cached responses
- Provide deterministic behavior for testing
"""

import hashlib
import json
import logging
import os
import time
from typing import Dict, Any, Optional, Union, Tuple
from enum import Enum
from diskcache import Cache
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class CacheBackend(Enum):
    """Available cache backends."""
    MEMORY = "memory"
    DISK = "disk"
    DISABLED = "disabled"


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    total_requests: int = 0
    cache_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            **asdict(self),
            "hit_rate": self.hit_rate
        }


class LLMCache:
    """
    LLM response cache with multiple backend support.
    
    Supports in-memory and disk-based caching with TTL,
    cache key generation, and performance metrics.
    """
    
    def __init__(
        self,
        backend: Union[CacheBackend, str] = CacheBackend.DISK,
        cache_dir: str = ".llm_cache",
        ttl: Optional[int] = None,
        max_size: Optional[int] = None
    ):
        """
        Initialize LLM cache.
        
        Args:
            backend: Cache backend to use
            cache_dir: Directory for disk cache
            ttl: Time-to-live in seconds (None for no expiration)
            max_size: Maximum cache size in bytes (None for unlimited)
        """
        if isinstance(backend, str):
            backend = CacheBackend(backend)
        
        self.backend = backend
        self.ttl = ttl
        self.metrics = CacheMetrics()
        
        if backend == CacheBackend.DISK:
            # Initialize disk cache without size_limit if None
            cache_args = {"statistics": True}
            if max_size is not None:
                cache_args["size_limit"] = max_size
            self.cache = Cache(cache_dir, **cache_args)
        elif backend == CacheBackend.MEMORY:
            # Use a simple dict for memory cache
            self.cache = {}
            self.cache_metadata = {}
        else:
            self.cache = None
    
    def _generate_cache_key(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate a deterministic cache key from request parameters.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            SHA256 hash as cache key
        """
        # Create a deterministic representation of all parameters
        key_data = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # Sort keys for consistency
        key_str = json.dumps(key_data, sort_keys=True)
        
        # Generate SHA256 hash
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Optional[str]:
        """
        Get cached response if available.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            Cached response or None if not found
        """
        if self.backend == CacheBackend.DISABLED or self.cache is None:
            return None
        
        cache_key = self._generate_cache_key(
            prompt, system_prompt, model, temperature, max_tokens, **kwargs
        )
        
        self.metrics.total_requests += 1
        
        try:
            if self.backend == CacheBackend.MEMORY:
                if cache_key in self.cache:
                    # Check TTL if set
                    if self.ttl and cache_key in self.cache_metadata:
                        timestamp = self.cache_metadata[cache_key]
                        if time.time() - timestamp > self.ttl:
                            # Expired
                            del self.cache[cache_key]
                            del self.cache_metadata[cache_key]
                            self.metrics.misses += 1
                            return None
                    
                    self.metrics.hits += 1
                    logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                    return self.cache[cache_key]
            else:
                # Disk cache
                result = self.cache.get(cache_key)
                if result is not None:
                    self.metrics.hits += 1
                    logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                    return result
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        self.metrics.misses += 1
        logger.debug(f"Cache miss for key: {cache_key[:8]}...")
        return None
    
    def set(
        self,
        response: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> bool:
        """
        Cache LLM response.
        
        Args:
            response: LLM response to cache
            prompt: User prompt
            system_prompt: System prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            True if successfully cached
        """
        if self.backend == CacheBackend.DISABLED or self.cache is None:
            return False
        
        cache_key = self._generate_cache_key(
            prompt, system_prompt, model, temperature, max_tokens, **kwargs
        )
        
        try:
            if self.backend == CacheBackend.MEMORY:
                self.cache[cache_key] = response
                self.cache_metadata[cache_key] = time.time()
                self.metrics.cache_size = len(self.cache)
            else:
                # Disk cache with TTL
                if self.ttl:
                    self.cache.set(cache_key, response, expire=self.ttl)
                else:
                    self.cache.set(cache_key, response)
                self.metrics.cache_size = len(self.cache)
            
            logger.debug(f"Cached response for key: {cache_key[:8]}...")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cached entries.
        
        Returns:
            True if successfully cleared
        """
        if self.cache is None:
            return True
        
        try:
            if self.backend == CacheBackend.MEMORY:
                self.cache.clear()
                self.cache_metadata.clear()
            else:
                self.cache.clear()
            
            # Reset metrics
            self.metrics = CacheMetrics()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        metrics = self.metrics.to_dict()
        
        if self.backend == CacheBackend.DISK and self.cache:
            # Add disk cache specific stats
            try:
                stats = self.cache.stats()
                metrics.update({
                    "disk_hits": stats[0],
                    "disk_misses": stats[1]
                })
            except:
                pass
        
        return metrics
    
    def close(self):
        """Close cache connections."""
        if self.backend == CacheBackend.DISK and self.cache:
            self.cache.close()


class CachedLLMWrapper:
    """
    LLM wrapper with caching support.
    
    This wrapper adds caching functionality to any LLM wrapper
    that implements the standard interface.
    """
    
    def __init__(
        self,
        base_wrapper,
        cache_backend: Union[CacheBackend, str] = CacheBackend.DISK,
        cache_dir: str = ".llm_cache",
        ttl: Optional[int] = 3600 * 24 * 7,  # 1 week default
        bypass_cache: bool = False
    ):
        """
        Initialize cached LLM wrapper.
        
        Args:
            base_wrapper: Base LLM wrapper instance
            cache_backend: Cache backend to use
            cache_dir: Directory for disk cache
            ttl: Cache TTL in seconds
            bypass_cache: Whether to bypass cache (for testing)
        """
        self.base_wrapper = base_wrapper
        self.bypass_cache = bypass_cache
        
        # Initialize cache
        self.cache = LLMCache(
            backend=cache_backend,
            cache_dir=cache_dir,
            ttl=ttl
        )
    
    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> str:
        """
        Call LLM with caching support.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            use_cache: Override default cache behavior
            **kwargs: Additional parameters
            
        Returns:
            LLM response
        """
        # Determine if we should use cache
        should_use_cache = not self.bypass_cache
        if use_cache is not None:
            should_use_cache = use_cache
        
        # Check cache first
        if should_use_cache:
            cached_response = self.cache.get(
                prompt, system_prompt, model, temperature, max_tokens, **kwargs
            )
            if cached_response is not None:
                return cached_response
        
        # Call base wrapper
        response = self.base_wrapper.call_llm(
            prompt, system_prompt, model, temperature, max_tokens, **kwargs
        )
        
        # Cache the response
        if should_use_cache:
            self.cache.set(
                response, prompt, system_prompt, model, temperature, max_tokens, **kwargs
            )
        
        return response
    
    def call_llm_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        output_format: str = "yaml",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 3000,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> Union[Dict[str, Any], list]:
        """
        Call LLM expecting structured output with caching.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            output_format: Expected format
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            use_cache: Override default cache behavior
            **kwargs: Additional parameters
            
        Returns:
            Parsed structured data
        """
        # For structured calls, we cache the raw response
        # and let the base wrapper handle parsing
        return self.base_wrapper.call_llm_structured(
            prompt, system_prompt, output_format, model, temperature, max_tokens, **kwargs
        )
    
    def clear_cache(self) -> bool:
        """Clear the cache."""
        return self.cache.clear()
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        return self.cache.get_metrics()
    
    def __getattr__(self, name):
        """Forward other attributes to base wrapper."""
        return getattr(self.base_wrapper, name)