"""
Async batch processing utilities for parallel LLM operations.

This module provides utilities to convert sync BatchNode operations
to async parallel operations for improved performance.
"""

import asyncio
from typing import List, Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class AsyncBatchProcessor:
    """Processes batches of items in parallel using async operations."""
    
    def __init__(
        self,
        batch_size: int = 5,
        max_concurrent: int = 10
    ):
        """
        Initialize async batch processor.
        
        Args:
            batch_size: Number of items per batch
            max_concurrent: Maximum concurrent operations
        """
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch_async(
        self,
        items: List[Any],
        processor_func: Callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        Process items in parallel batches.
        
        Args:
            items: List of items to process
            processor_func: Async function to process each item
            *args, **kwargs: Additional arguments for processor_func
            
        Returns:
            List of results in same order as input
        """
        # Create batches
        batches = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batches.append(batch)
        
        # Process batches
        all_results = []
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} items)")
            
            # Process items in batch concurrently
            tasks = []
            for item in batch:
                task = self._process_with_semaphore(
                    processor_func, item, *args, **kwargs
                )
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing item {idx} in batch {batch_idx}: {result}")
                    # You might want to handle this differently
                    all_results.append(None)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def _process_with_semaphore(
        self,
        processor_func: Callable,
        item: Any,
        *args,
        **kwargs
    ) -> Any:
        """Process single item with semaphore control."""
        async with self.semaphore:
            try:
                return await processor_func(item, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in async processing: {e}")
                raise


def create_async_batch_node(
    sync_node_class,
    async_llm_wrapper,
    batch_size: int = 5,
    max_concurrent: int = 10
):
    """
    Factory function to create async version of a BatchNode.
    
    Args:
        sync_node_class: The synchronous BatchNode class
        async_llm_wrapper: Async LLM wrapper instance
        batch_size: Items per batch
        max_concurrent: Max concurrent operations
        
    Returns:
        Async version of the node class
    """
    from pocketflow import AsyncParallelBatchNode
    
    class AsyncVersion(AsyncParallelBatchNode):
        """Async parallel version of the node."""
        
        def __init__(self):
            super().__init__()
            self.llm = async_llm_wrapper
            self.batch_size = batch_size
            self.processor = AsyncBatchProcessor(batch_size, max_concurrent)
            
            # Copy any other attributes from sync version
            if hasattr(sync_node_class, '__init__'):
                # Get default instance to copy attributes
                try:
                    sync_instance = sync_node_class()
                    for attr in ['max_retries', 'wait']:
                        if hasattr(sync_instance, attr):
                            setattr(self, attr, getattr(sync_instance, attr))
                except:
                    pass
        
        async def prep_async(self, shared: dict) -> List[Any]:
            """Async version of prep - delegates to sync version."""
            # Most prep methods just read from shared store
            # so they can remain synchronous
            sync_instance = sync_node_class()
            return sync_instance.prep(shared)
        
        async def exec_async(self, item: Any) -> Any:
            """Process single item asynchronously."""
            # This will be called by AsyncParallelBatchNode for each item
            # The actual implementation depends on the specific node
            raise NotImplementedError(
                "Subclass must implement exec_async for item processing"
            )
        
        async def post_async(
            self,
            shared: dict,
            prep_res: Any,
            exec_res: List[Any]
        ) -> Optional[str]:
            """Async version of post - delegates to sync version."""
            sync_instance = sync_node_class()
            return sync_instance.post(shared, prep_res, exec_res)
    
    # Set the class name
    AsyncVersion.__name__ = f"Async{sync_node_class.__name__}"
    AsyncVersion.__qualname__ = f"Async{sync_node_class.__name__}"
    
    return AsyncVersion