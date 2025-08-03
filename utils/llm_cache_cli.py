#!/usr/bin/env python3
"""
Command-line interface for managing LLM cache.

This module provides commands to inspect, clear, and manage the LLM cache.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.llm_cache import LLMCache, CacheBackend


def format_bytes(size: int) -> str:
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM Cache Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cache statistics
  python -m utils.llm_cache_cli stats
  
  # Clear the cache
  python -m utils.llm_cache_cli clear
  
  # Show cache configuration
  python -m utils.llm_cache_cli info
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    stats_parser.add_argument(
        '--cache-dir',
        default=os.getenv('LLM_CACHE_DIR', '.llm_cache'),
        help='Cache directory (default: .llm_cache or LLM_CACHE_DIR env var)'
    )
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear the cache')
    clear_parser.add_argument(
        '--cache-dir',
        default=os.getenv('LLM_CACHE_DIR', '.llm_cache'),
        help='Cache directory (default: .llm_cache or LLM_CACHE_DIR env var)'
    )
    clear_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show cache configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'info':
        # Show current configuration
        print("LLM Cache Configuration:")
        print(f"  Enabled: {os.getenv('ENABLE_LLM_CACHE', 'false')}")
        print(f"  Backend: {os.getenv('LLM_CACHE_BACKEND', 'disk')}")
        print(f"  Directory: {os.getenv('LLM_CACHE_DIR', '.llm_cache')}")
        print(f"  TTL: {os.getenv('LLM_CACHE_TTL', str(3600 * 24 * 7))} seconds")
        print("\nTo enable caching, set environment variable:")
        print("  export ENABLE_LLM_CACHE=true")
        return 0
    
    # Initialize cache for stats/clear commands
    cache = LLMCache(
        backend=CacheBackend.DISK,
        cache_dir=args.cache_dir
    )
    
    if args.command == 'stats':
        # Show cache statistics
        metrics = cache.get_metrics()
        
        print(f"LLM Cache Statistics ({args.cache_dir}):")
        print(f"  Total requests: {metrics['total_requests']}")
        print(f"  Cache hits: {metrics['hits']}")
        print(f"  Cache misses: {metrics['misses']}")
        print(f"  Hit rate: {metrics['hit_rate']:.1%}")
        print(f"  Cache entries: {metrics['cache_size']}")
        
        # Try to get disk usage
        cache_path = Path(args.cache_dir)
        if cache_path.exists():
            total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
            print(f"  Disk usage: {format_bytes(total_size)}")
    
    elif args.command == 'clear':
        # Clear the cache
        if not args.confirm:
            response = input(f"Clear cache at {args.cache_dir}? [y/N] ")
            if response.lower() != 'y':
                print("Cancelled")
                return 0
        
        if cache.clear():
            print(f"Cache cleared successfully: {args.cache_dir}")
        else:
            print(f"Failed to clear cache: {args.cache_dir}")
            return 1
    
    cache.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())