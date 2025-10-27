#!/usr/bin/env python3
"""
Script to delete consolidated_datasets.json and thumbnails folder.
"""

import os
import shutil
from pathlib import Path

def main():
    # Get the project root directory (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define paths to delete
    json_file = project_root / "docs" / "assets" / "dataset_info" / "consolidated_datasets.json"
    thumbnails_dir = project_root / "docs" / "assets" / "thumbnails"
    
    # Delete consolidated_datasets.json
    if json_file.exists():
        try:
            json_file.unlink()
            print(f"✓ Deleted: {json_file}")
        except Exception as e:
            print(f"✗ Error deleting {json_file}: {e}")
    else:
        print(f"- File not found: {json_file}")
    
    # Delete thumbnails folder
    if thumbnails_dir.exists() and thumbnails_dir.is_dir():
        try:
            shutil.rmtree(thumbnails_dir)
            print(f"✓ Deleted: {thumbnails_dir}")
        except Exception as e:
            print(f"✗ Error deleting {thumbnails_dir}: {e}")
    else:
        print(f"- Directory not found: {thumbnails_dir}")
    
    print("\nCleanup complete!")

if __name__ == "__main__":
    main()

