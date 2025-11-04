#!/usr/bin/env python3
"""
Test script to demonstrate the performance improvement of the optimized data loader.
"""

import sys
import time
import logging
from src.data.data_loader import DataLoader

# Configure logging to see the detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def test_loader(url: str, use_optimized: bool = True):
    """Test the data loader with timing."""
    loader = DataLoader()

    mode = "OPTIMIZED" if use_optimized else "TRADITIONAL"
    print(f"\n{'='*70}")
    print(f" Testing {mode} Loader")
    print(f"{'='*70}")

    start_time = time.time()
    success = loader.load(url, use_optimized=use_optimized)
    elapsed = time.time() - start_time

    if success:
        print(f"\n✓ {mode} loading completed successfully!")
        print(f"  - Total time: {elapsed:.2f} seconds")
        print(f"  - Channels loaded: {len(loader.channels)}")
        print(f"  - Groups found: {len(loader.groups)}")

        # Show some sample groups
        if loader.groups:
            print(f"\n  Sample groups:")
            for i, (group_name, group) in enumerate(list(loader.groups.items())[:5]):
                print(f"    {i+1}. {group_name}: {len(group.channels)} channels")
    else:
        print(f"✗ {mode} loading failed!")

    return elapsed, success

if __name__ == "__main__":
    # Test URL - using a public IPTV playlist
    test_url = "https://iptv-org.github.io/iptv/countries/il.m3u"

    print("\n" + "="*70)
    print(" IPTV Data Loader Performance Comparison")
    print("="*70)
    print(f"\nTest URL: {test_url}")

    # Test traditional loader
    traditional_time, traditional_success = test_loader(test_url, use_optimized=False)

    # Test optimized loader
    optimized_time, optimized_success = test_loader(test_url, use_optimized=True)

    # Compare results
    if traditional_success and optimized_success:
        print(f"\n{'='*70}")
        print(" Performance Comparison Results")
        print(f"{'='*70}")
        print(f"  Traditional loader: {traditional_time:.2f} seconds")
        print(f"  Optimized loader:   {optimized_time:.2f} seconds")

        if optimized_time < traditional_time:
            speedup = traditional_time / optimized_time
            time_saved = traditional_time - optimized_time
            print(f"\n  🚀 Speedup: {speedup:.2f}x faster!")
            print(f"  ⏱️  Time saved: {time_saved:.2f} seconds")
            print(f"  📊 Performance improvement: {((speedup - 1) * 100):.1f}%")
        else:
            print(f"\n  Note: Results may vary based on network conditions")

    print(f"\n{'='*70}\n")
