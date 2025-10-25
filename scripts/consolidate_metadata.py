#!/usr/bin/env python3
"""
Metadata Consolidation Script
==============================

This script consolidates all individual YAML metadata files into a single
optimized JSON file, dramatically reducing HTTP requests.

This addresses the #1 CRITICAL bottleneck: reducing 2000+ HTTP requests to just 1.

Usage:
    python consolidate_metadata.py [--input-dir INPUT] [--output OUTPUT]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List
import gzip

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required for this script.")
    print("Install with: pip install pyyaml")
    sys.exit(1)


def load_yaml_file(file_path: Path) -> Dict:
    """Load and parse a single YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data
    except Exception as e:
        print(f"Warning: Failed to parse {file_path.name}: {e}")
        return None


def consolidate_metadata(input_dir: str, output_file: str, compress: bool = True):
    """
    Consolidate all YAML files into a single JSON file.
    
    Args:
        input_dir: Directory containing YAML files
        output_file: Output JSON file path
        compress: Whether to create a compressed .gz version
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory not found: {input_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("Metadata Consolidation Script")
    print("=" * 80)
    print()
    print(f"Input directory: {input_path}")
    print(f"Output file: {output_file}")
    print()
    
    # Find all YAML files
    yml_files = list(input_path.glob("*.yml"))
    yaml_files = list(input_path.glob("*.yaml"))
    all_files = yml_files + yaml_files
    
    print(f"Found {len(all_files)} YAML files")
    print()
    
    if len(all_files) == 0:
        print("No YAML files found. Exiting.")
        sys.exit(1)
    
    # Load and consolidate
    print("Loading and parsing YAML files...")
    consolidated = {}
    failed_count = 0
    
    for i, file_path in enumerate(all_files, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(all_files)} files...")
        
        # Use filename without extension as key
        key = file_path.stem
        
        data = load_yaml_file(file_path)
        if data is not None:
            consolidated[key] = data
        else:
            failed_count += 1
    
    print(f"✓ Successfully loaded {len(consolidated)} files")
    if failed_count > 0:
        print(f"✗ Failed to load {failed_count} files")
    print()
    
    # Save consolidated JSON
    print(f"Saving consolidated JSON to {output_file}...")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, ensure_ascii=False, separators=(',', ':'))
    
    original_size = os.path.getsize(output_file)
    print(f"✓ Saved {output_file}")
    print(f"  Size: {original_size / 1024:.2f} KB ({original_size / (1024*1024):.2f} MB)")
    print()
    
    # Create compressed version
    if compress:
        print("Creating compressed version...")
        compressed_file = output_file + ".gz"
        
        with open(output_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb', compresslevel=9) as f_out:
                f_out.write(f_in.read())
        
        compressed_size = os.path.getsize(compressed_file)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        print(f"✓ Saved {compressed_file}")
        print(f"  Size: {compressed_size / 1024:.2f} KB ({compressed_size / (1024*1024):.2f} MB)")
        print(f"  Compression: {compression_ratio:.1f}% reduction")
        print()
    
    # Calculate savings
    print("=" * 80)
    print("PERFORMANCE IMPACT")
    print("=" * 80)
    print()
    print(f"Before: {len(all_files)} HTTP requests")
    print(f"After:  1 HTTP request")
    print(f"Reduction: {len(all_files) - 1} fewer requests ({(len(all_files)-1)/len(all_files)*100:.1f}% reduction)")
    print()
    
    # Calculate estimated load time improvement
    # Assume ~50ms latency per request on GitHub Pages
    before_time = len(all_files) * 0.05  # seconds
    after_time = 0.05  # single request
    time_saved = before_time - after_time
    
    print(f"Estimated load time (assuming 50ms per request):")
    print(f"  Before: {before_time:.1f}s")
    print(f"  After:  {after_time:.1f}s")
    print(f"  Saved:  {time_saved:.1f}s ({time_saved/before_time*100:.1f}% faster)")
    print()
    
    # Next steps
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. Update your JavaScript to load the consolidated JSON:")
    print()
    print("   // OLD: Sequential YAML loading")
    print("   // const fileList = await fetch('data_index.json').then(r => r.json());")
    print("   // for (const file of fileList) {")
    print("   //   const data = await fetch(file).then(r => r.text());")
    print("   //   const parsed = jsyaml.load(data);")
    print("   // }")
    print()
    print("   // NEW: Single JSON load")
    print("   const allData = await fetch('consolidated_datasets.json')")
    print("     .then(r => r.json());")
    print("   ")
    print("   // allData is now an object with all datasets")
    print("   // Key = filename (without .yml extension)")
    print("   // Value = dataset metadata")
    print()
    print("2. Test the changes locally first")
    print()
    print("3. Deploy to GitHub Pages")
    print()
    print("4. Verify the performance improvement using browser DevTools")
    print()
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidate YAML metadata files into a single JSON file"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="docs/assets/dataset_info",
        help="Directory containing YAML files (default: docs/assets/dataset_info)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/assets/dataset_info/consolidated_datasets.json",
        help="Output JSON file path (default: docs/assets/dataset_info/consolidated_datasets.json)"
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Skip creating compressed .gz version"
    )
    
    args = parser.parse_args()
    
    consolidate_metadata(
        input_dir=args.input_dir,
        output_file=args.output,
        compress=not args.no_compress
    )


if __name__ == "__main__":
    main()

