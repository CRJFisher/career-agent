"""
Benchmark script to compare sequential vs parallel LLM calls.

This script demonstrates the performance improvement from parallel LLM calls.
"""

import asyncio
import time
import os
import sys
from typing import List
from unittest.mock import Mock, AsyncMock
import argparse

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment for testing without real API calls
os.environ["OPENROUTER_API_KEY"] = "test-key"


def create_mock_sync_wrapper():
    """Create mock sync LLM wrapper for benchmarking."""
    from utils.llm_wrapper import LLMWrapper
    
    wrapper = Mock(spec=LLMWrapper)
    
    def mock_call(prompt, **kwargs):
        # Simulate API latency
        time.sleep(0.5)
        return f"Response to: {prompt[:20]}..."
    
    wrapper.call_llm = mock_call
    wrapper.call_llm_structured = mock_call
    
    return wrapper


async def create_mock_async_wrapper():
    """Create mock async LLM wrapper for benchmarking."""
    from utils.async_llm_wrapper import AsyncLLMWrapper
    
    wrapper = Mock(spec=AsyncLLMWrapper)
    
    async def mock_call(prompt, **kwargs):
        # Simulate API latency
        await asyncio.sleep(0.5)
        return f"Response to: {prompt[:20]}..."
    
    wrapper.call_llm = mock_call
    wrapper.call_llm_structured = mock_call
    wrapper.close = AsyncMock()
    
    return wrapper


def benchmark_sequential(num_documents: int = 10):
    """Benchmark sequential processing."""
    print(f"\nBenchmarking SEQUENTIAL processing of {num_documents} documents...")
    
    # Create mock documents
    documents = [
        {"name": f"document_{i}.pdf", "content": f"Document {i} content..."}
        for i in range(num_documents)
    ]
    
    # Mock LLM wrapper
    wrapper = create_mock_sync_wrapper()
    
    start_time = time.time()
    results = []
    
    for i, doc in enumerate(documents):
        print(f"  Processing document {i+1}/{num_documents}...", end="\r")
        
        # Simulate extraction prompt
        prompt = f"Extract experiences from {doc['name']}: {doc['content']}"
        result = wrapper.call_llm(prompt)
        results.append(result)
    
    elapsed = time.time() - start_time
    
    print(f"\nSequential processing completed:")
    print(f"  Total time: {elapsed:.2f} seconds")
    print(f"  Average per document: {elapsed/num_documents:.2f} seconds")
    print(f"  Documents per second: {num_documents/elapsed:.2f}")
    
    return elapsed


async def benchmark_parallel(num_documents: int = 10, max_concurrent: int = 5):
    """Benchmark parallel processing."""
    print(f"\nBenchmarking PARALLEL processing of {num_documents} documents (max {max_concurrent} concurrent)...")
    
    # Create mock documents
    documents = [
        {"name": f"document_{i}.pdf", "content": f"Document {i} content..."}
        for i in range(num_documents)
    ]
    
    # Mock async LLM wrapper
    wrapper = await create_mock_async_wrapper()
    
    start_time = time.time()
    
    # Process with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_document(doc, index):
        async with semaphore:
            print(f"  Processing document {index+1}/{num_documents}...", end="\r")
            prompt = f"Extract experiences from {doc['name']}: {doc['content']}"
            return await wrapper.call_llm(prompt)
    
    # Create all tasks
    tasks = [
        process_document(doc, i)
        for i, doc in enumerate(documents)
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    
    print(f"\nParallel processing completed:")
    print(f"  Total time: {elapsed:.2f} seconds")
    print(f"  Average per document: {elapsed/num_documents:.2f} seconds")
    print(f"  Documents per second: {num_documents/elapsed:.2f}")
    print(f"  Speedup: {num_documents * 0.5 / elapsed:.1f}x")
    
    await wrapper.close()
    
    return elapsed


async def benchmark_batch_sizes(num_documents: int = 20):
    """Benchmark different batch sizes."""
    print(f"\nBenchmarking different batch sizes for {num_documents} documents...")
    print("-" * 60)
    
    batch_sizes = [1, 3, 5, 10, 20]
    results = []
    
    for batch_size in batch_sizes:
        if batch_size > num_documents:
            continue
        
        elapsed = await benchmark_parallel(num_documents, batch_size)
        speedup = (num_documents * 0.5) / elapsed
        results.append((batch_size, elapsed, speedup))
    
    print("\nSummary:")
    print(f"{'Batch Size':>12} | {'Total Time':>12} | {'Speedup':>10}")
    print("-" * 40)
    for batch_size, elapsed, speedup in results:
        print(f"{batch_size:>12} | {elapsed:>11.2f}s | {speedup:>9.1f}x")


async def main():
    """Run benchmarks."""
    parser = argparse.ArgumentParser(
        description="Benchmark parallel LLM performance"
    )
    parser.add_argument(
        "--documents",
        type=int,
        default=10,
        help="Number of documents to process"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum concurrent LLM calls"
    )
    parser.add_argument(
        "--compare-batch-sizes",
        action="store_true",
        help="Compare different batch sizes"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LLM Parallel Processing Benchmark")
    print("=" * 60)
    print("\nNote: Using mock LLM calls with 0.5s simulated latency")
    
    # Run sequential benchmark
    seq_time = benchmark_sequential(args.documents)
    
    # Run parallel benchmark
    par_time = await benchmark_parallel(args.documents, args.max_concurrent)
    
    # Show comparison
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"Documents processed: {args.documents}")
    print(f"Sequential time: {seq_time:.2f}s")
    print(f"Parallel time: {par_time:.2f}s")
    print(f"Speedup: {seq_time/par_time:.1f}x faster")
    print(f"Time saved: {seq_time - par_time:.2f}s ({(1 - par_time/seq_time)*100:.0f}%)")
    
    # Optional: test different batch sizes
    if args.compare_batch_sizes:
        await benchmark_batch_sizes(args.documents)


if __name__ == "__main__":
    asyncio.run(main())