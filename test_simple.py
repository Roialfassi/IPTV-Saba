#!/usr/bin/env python3
"""
Simple test to verify the optimized loader works correctly.
"""

import sys
import logging
from src.data.data_loader import DataLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def test_file_loader():
    """Test with local file."""
    print("\n" + "="*70)
    print(" Testing DataLoader with Local File")
    print("="*70)

    loader = DataLoader()
    test_file = "test_sample.m3u"

    print(f"\nLoading from: {test_file}")
    success = loader.load(test_file)

    if success:
        print(f"\n✓ Loading successful!")
        print(f"  - Channels loaded: {len(loader.channels)}")
        print(f"  - Groups found: {len(loader.groups)}")
        print(f"\nGroups and channels:")
        for group_name, group in loader.groups.items():
            print(f"  • {group_name}: {len(group.channels)} channel(s)")
            for channel in group.channels:
                print(f"    - {channel.name}")
        return True
    else:
        print(f"\n✗ Loading failed!")
        return False

if __name__ == "__main__":
    test_file_loader()
