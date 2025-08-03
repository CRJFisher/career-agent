"""
Unit tests for LLM caching functionality.
"""

import os
import tempfile
import time
from unittest.mock import Mock, patch
import pytest

from utils.llm_cache import (
    LLMCache,
    CacheBackend,
    CacheMetrics,
    CachedLLMWrapper
)


class TestLLMCache:
    """Test suite for LLMCache class."""
    
    def test_cache_key_generation(self):
        """Test that cache keys are deterministic and unique."""
        cache = LLMCache(backend=CacheBackend.MEMORY)
        
        # Same parameters should generate same key
        key1 = cache._generate_cache_key(
            prompt="Test prompt",
            model="gpt-4",
            temperature=0.7
        )
        key2 = cache._generate_cache_key(
            prompt="Test prompt",
            model="gpt-4",
            temperature=0.7
        )
        assert key1 == key2
        
        # Different parameters should generate different keys
        key3 = cache._generate_cache_key(
            prompt="Test prompt",
            model="gpt-4",
            temperature=0.8  # Different temperature
        )
        assert key1 != key3
        
        # Order of kwargs shouldn't matter
        key4 = cache._generate_cache_key(
            prompt="Test prompt",
            temperature=0.7,
            model="gpt-4"
        )
        assert key1 == key4
    
    def test_memory_cache_operations(self):
        """Test basic memory cache operations."""
        cache = LLMCache(backend=CacheBackend.MEMORY)
        
        # Test cache miss
        result = cache.get(prompt="Test prompt")
        assert result is None
        assert cache.metrics.misses == 1
        assert cache.metrics.hits == 0
        
        # Test cache set
        success = cache.set(
            response="Test response",
            prompt="Test prompt"
        )
        assert success is True
        assert cache.metrics.cache_size == 1
        
        # Test cache hit
        result = cache.get(prompt="Test prompt")
        assert result == "Test response"
        assert cache.metrics.hits == 1
        assert cache.metrics.misses == 1
        
        # Test cache clear
        success = cache.clear()
        assert success is True
        assert cache.metrics.hits == 0
        assert cache.metrics.misses == 0
        assert cache.metrics.cache_size == 0
    
    def test_disk_cache_operations(self):
        """Test basic disk cache operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMCache(
                backend=CacheBackend.DISK,
                cache_dir=tmpdir,
                ttl=3600  # Set explicit TTL to avoid None issues
            )
            
            # Test cache operations
            result = cache.get(prompt="Test prompt")
            assert result is None
            
            success = cache.set(
                response="Test response",
                prompt="Test prompt"
            )
            assert success is True
            
            result = cache.get(prompt="Test prompt")
            assert result == "Test response"
            
            # Close and reopen to test persistence
            cache.close()
            
            cache2 = LLMCache(
                backend=CacheBackend.DISK,
                cache_dir=tmpdir
            )
            result = cache2.get(prompt="Test prompt")
            assert result == "Test response"
            cache2.close()
    
    def test_ttl_expiration(self):
        """Test TTL expiration for memory cache."""
        cache = LLMCache(
            backend=CacheBackend.MEMORY,
            ttl=1  # 1 second TTL
        )
        
        # Set a value
        cache.set(
            response="Test response",
            prompt="Test prompt"
        )
        
        # Should be available immediately
        result = cache.get(prompt="Test prompt")
        assert result == "Test response"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        result = cache.get(prompt="Test prompt")
        assert result is None
    
    def test_disabled_cache(self):
        """Test that disabled cache doesn't store anything."""
        cache = LLMCache(backend=CacheBackend.DISABLED)
        
        # Should not cache
        success = cache.set(
            response="Test response",
            prompt="Test prompt"
        )
        assert success is False
        
        # Should not retrieve
        result = cache.get(prompt="Test prompt")
        assert result is None
    
    def test_cache_metrics(self):
        """Test cache metrics calculation."""
        cache = LLMCache(backend=CacheBackend.MEMORY)
        
        # Initial metrics
        metrics = cache.get_metrics()
        assert metrics['hits'] == 0
        assert metrics['misses'] == 0
        assert metrics['hit_rate'] == 0.0
        
        # Generate some activity
        cache.get(prompt="Test 1")  # Miss
        cache.set("Response 1", prompt="Test 1")
        cache.get(prompt="Test 1")  # Hit
        cache.get(prompt="Test 2")  # Miss
        
        metrics = cache.get_metrics()
        assert metrics['hits'] == 1
        assert metrics['misses'] == 2
        assert metrics['total_requests'] == 3
        assert metrics['hit_rate'] == 1/3


class TestCachedLLMWrapper:
    """Test suite for CachedLLMWrapper class."""
    
    def test_wrapper_with_cache_hit(self):
        """Test wrapper returns cached response on hit."""
        # Mock base wrapper
        base_wrapper = Mock()
        base_wrapper.call_llm.return_value = "Fresh response"
        
        # Create cached wrapper
        cached_wrapper = CachedLLMWrapper(
            base_wrapper=base_wrapper,
            cache_backend=CacheBackend.MEMORY
        )
        
        # First call should hit base wrapper
        result1 = cached_wrapper.call_llm(prompt="Test prompt")
        assert result1 == "Fresh response"
        assert base_wrapper.call_llm.call_count == 1
        
        # Second call should hit cache
        result2 = cached_wrapper.call_llm(prompt="Test prompt")
        assert result2 == "Fresh response"
        assert base_wrapper.call_llm.call_count == 1  # Not called again
    
    def test_wrapper_cache_bypass(self):
        """Test wrapper can bypass cache."""
        base_wrapper = Mock()
        base_wrapper.call_llm.return_value = "Response"
        
        cached_wrapper = CachedLLMWrapper(
            base_wrapper=base_wrapper,
            cache_backend=CacheBackend.MEMORY,
            bypass_cache=True
        )
        
        # Should always call base wrapper
        result1 = cached_wrapper.call_llm(prompt="Test prompt")
        result2 = cached_wrapper.call_llm(prompt="Test prompt")
        assert base_wrapper.call_llm.call_count == 2
    
    def test_wrapper_per_call_cache_control(self):
        """Test per-call cache control."""
        base_wrapper = Mock()
        base_wrapper.call_llm.return_value = "Response"
        
        cached_wrapper = CachedLLMWrapper(
            base_wrapper=base_wrapper,
            cache_backend=CacheBackend.MEMORY
        )
        
        # First call with cache
        result1 = cached_wrapper.call_llm(
            prompt="Test prompt",
            use_cache=True
        )
        assert base_wrapper.call_llm.call_count == 1
        
        # Second call without cache
        result2 = cached_wrapper.call_llm(
            prompt="Test prompt",
            use_cache=False
        )
        assert base_wrapper.call_llm.call_count == 2
    
    def test_wrapper_forwards_attributes(self):
        """Test wrapper forwards unknown attributes to base."""
        base_wrapper = Mock()
        base_wrapper.some_method = Mock(return_value="Result")
        base_wrapper.some_attribute = "Value"
        
        cached_wrapper = CachedLLMWrapper(
            base_wrapper=base_wrapper,
            cache_backend=CacheBackend.MEMORY
        )
        
        # Should forward method calls
        result = cached_wrapper.some_method(arg1="test")
        assert result == "Result"
        base_wrapper.some_method.assert_called_with(arg1="test")
        
        # Should forward attribute access
        assert cached_wrapper.some_attribute == "Value"
    
    def test_wrapper_structured_calls(self):
        """Test wrapper handles structured LLM calls."""
        base_wrapper = Mock()
        base_wrapper.call_llm_structured.return_value = {"key": "value"}
        
        cached_wrapper = CachedLLMWrapper(
            base_wrapper=base_wrapper,
            cache_backend=CacheBackend.MEMORY
        )
        
        result = cached_wrapper.call_llm_structured(
            prompt="Test prompt",
            output_format="json"
        )
        assert result == {"key": "value"}
        base_wrapper.call_llm_structured.assert_called_once()


class TestIntegration:
    """Integration tests with actual LLM wrapper."""
    
    @patch.dict(os.environ, {"ENABLE_LLM_CACHE": "true"})
    def test_get_default_wrapper_with_cache(self):
        """Test get_default_llm_wrapper enables caching from env."""
        from utils.llm_wrapper import get_default_llm_wrapper
        
        # Reset global wrapper
        import utils.llm_wrapper
        utils.llm_wrapper._default_wrapper = None
        
        with patch('utils.llm_wrapper.LLMWrapper'):
            wrapper = get_default_llm_wrapper()
            
            # Should be wrapped with cache
            from utils.llm_cache import CachedLLMWrapper
            assert isinstance(wrapper, CachedLLMWrapper)
    
    @patch.dict(os.environ, {"ENABLE_LLM_CACHE": "false"})
    def test_get_default_wrapper_without_cache(self):
        """Test get_default_llm_wrapper without caching."""
        from utils.llm_wrapper import get_default_llm_wrapper, LLMWrapper
        
        # Reset global wrapper
        import utils.llm_wrapper
        utils.llm_wrapper._default_wrapper = None
        
        with patch('utils.llm_wrapper.LLMWrapper') as MockWrapper:
            wrapper = get_default_llm_wrapper()
            
            # Should be base wrapper
            assert wrapper == MockWrapper.return_value