#!/usr/bin/env python3
"""
Optimization Initialization Script
===================================

This script automatically runs all performance optimizations for the RoboCOIN
Dataset Visualizer. It checks if optimized assets already exist and only
generates what's missing.

Usage:
    python opti_init.py [--force] [--skip-thumbnails] [--skip-consolidation]

This should be run as a pre-processing step before deploying the HTML app.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(text):
    """Print a formatted section header."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}[{text}]{Colors.ENDC}")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_dependency(command, install_cmd=None):
    """Check if a command is available."""
    try:
        subprocess.run([command, '--version'], 
                      capture_output=True, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def install_pyyaml():
    """Install PyYAML if not present."""
    print_info("Installing PyYAML...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyyaml'],
                      check=True,
                      capture_output=True)
        print_success("PyYAML installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install PyYAML: {e}")
        return False


def check_consolidated_json(docs_dir):
    """Check if consolidated JSON exists."""
    json_path = docs_dir / "assets" / "dataset_info" / "consolidated_datasets.json"
    json_gz_path = Path(str(json_path) + ".gz")
    
    if json_path.exists():
        size_mb = json_path.stat().st_size / (1024 * 1024)
        print_success(f"Consolidated JSON exists: {json_path.name} ({size_mb:.2f} MB)")
        
        if json_gz_path.exists():
            gz_size_kb = json_gz_path.stat().st_size / 1024
            print_success(f"Compressed version exists: {json_gz_path.name} ({gz_size_kb:.2f} KB)")
        
        return True
    
    return False


def check_thumbnails(docs_dir):
    """Check if thumbnails directory exists and has files."""
    thumbnails_dir = docs_dir / "assets" / "thumbnails"
    
    if not thumbnails_dir.exists():
        return False
    
    thumbnail_files = list(thumbnails_dir.glob("*.jpg"))
    
    if len(thumbnail_files) == 0:
        return False
    
    total_size = sum(f.stat().st_size for f in thumbnail_files)
    size_mb = total_size / (1024 * 1024)
    print_success(f"Thumbnails exist: {len(thumbnail_files)} files ({size_mb:.2f} MB)")
    
    return True


def run_consolidation(project_root, force=False):
    """Run the consolidation script."""
    print_section("Step 1: Consolidating YAML files")
    
    docs_dir = project_root / "docs"
    
    if not force and check_consolidated_json(docs_dir):
        print_info("Consolidated JSON already exists. Skipping...")
        print_info("Use --force to regenerate.")
        return True
    
    # Check dependencies
    if not check_python_package('yaml'):
        print_warning("PyYAML not found.")
        if not install_pyyaml():
            print_error("Cannot proceed without PyYAML")
            return False
    
    # Run consolidation script
    consolidate_script = project_root / "scripts" / "consolidate_metadata.py"
    
    if not consolidate_script.exists():
        print_error(f"Consolidation script not found: {consolidate_script}")
        return False
    
    print_info("Running consolidation script...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(consolidate_script)],
            cwd=str(project_root),
            check=True,
            capture_output=False
        )
        
        print_success("Consolidation complete!")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Consolidation failed: {e}")
        return False


def run_thumbnail_generation(project_root, force=False):
    """Run the thumbnail generation script."""
    print_section("Step 2: Generating video thumbnails")
    
    docs_dir = project_root / "docs"
    
    if not force and check_thumbnails(docs_dir):
        print_info("Thumbnails already exist. Skipping...")
        print_info("Use --force to regenerate.")
        return True
    
    # Check for ffmpeg
    if not check_dependency('ffmpeg'):
        print_error("ffmpeg is not installed or not in PATH")
        print_info("Install ffmpeg:")
        print_info("  Ubuntu/Debian: sudo apt install ffmpeg")
        print_info("  macOS: brew install ffmpeg")
        print_info("  Windows: Download from https://ffmpeg.org/download.html")
        return False
    
    print_success("ffmpeg is available")
    
    # Run thumbnail generation script
    thumbnail_script = project_root / "scripts" / "generate_thumbnails.py"
    
    if not thumbnail_script.exists():
        print_error(f"Thumbnail script not found: {thumbnail_script}")
        return False
    
    print_info("Running thumbnail generation script...")
    print_info("This may take a few minutes for 2000 videos...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(thumbnail_script), '--workers', '8'],
            cwd=str(project_root),
            check=True,
            capture_output=False
        )
        
        print_success("Thumbnail generation complete!")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Thumbnail generation failed: {e}")
        return False


def verify_optimizations(docs_dir):
    """Verify that all optimizations are in place."""
    print_section("Verification")
    
    all_good = True
    
    # Check consolidated JSON
    json_path = docs_dir / "assets" / "dataset_info" / "consolidated_datasets.json"
    if json_path.exists():
        print_success(f"✓ Consolidated JSON: {json_path}")
    else:
        print_error(f"✗ Missing: {json_path}")
        all_good = False
    
    # Check thumbnails
    thumbnails_dir = docs_dir / "assets" / "thumbnails"
    if thumbnails_dir.exists():
        count = len(list(thumbnails_dir.glob("*.jpg")))
        if count > 0:
            print_success(f"✓ Thumbnails: {count} files in {thumbnails_dir}")
        else:
            print_warning(f"⚠ Thumbnails directory exists but is empty: {thumbnails_dir}")
            all_good = False
    else:
        print_error(f"✗ Missing: {thumbnails_dir}")
        all_good = False
    
    return all_good


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run all performance optimizations for RoboCOIN Dataset Visualizer"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if outputs exist'
    )
    parser.add_argument(
        '--skip-consolidation',
        action='store_true',
        help='Skip YAML consolidation step'
    )
    parser.add_argument(
        '--skip-thumbnails',
        action='store_true',
        help='Skip thumbnail generation step'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Path to project root (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Determine project root
    project_root = Path(args.project_root).resolve()
    docs_dir = project_root / "docs"
    
    # Print header
    print_header("RoboCOIN Optimization Initialization")
    
    print(f"Project root: {project_root}")
    print(f"Docs directory: {docs_dir}")
    
    if not docs_dir.exists():
        print_error(f"Docs directory not found: {docs_dir}")
        print_error("Make sure you're running this from the project root.")
        sys.exit(1)
    
    # Track success
    success = True
    
    # Step 1: Consolidation
    if not args.skip_consolidation:
        if not run_consolidation(project_root, args.force):
            success = False
            print_error("Consolidation failed!")
    else:
        print_warning("Skipping consolidation (--skip-consolidation)")
    
    # Step 2: Thumbnails
    if not args.skip_thumbnails:
        if not run_thumbnail_generation(project_root, args.force):
            success = False
            print_error("Thumbnail generation failed!")
            print_info("You can skip thumbnails with --skip-thumbnails if ffmpeg is not available")
    else:
        print_warning("Skipping thumbnail generation (--skip-thumbnails)")
    
    # Verification
    if success:
        if verify_optimizations(docs_dir):
            print_section("Summary")
            print_success("All optimizations completed successfully!")
            print()
            print_info("Next steps:")
            print("  1. Test locally: cd docs && python -m http.server 8000")
            print("  2. Open http://localhost:8000 in your browser")
            print("  3. Check Chrome DevTools Network tab for improvements")
            print("  4. Deploy to GitHub Pages: git add . && git commit && git push")
            print()
            print_header("🎉 Ready to Deploy!")
            return 0
        else:
            print_error("Some optimizations are missing. Check errors above.")
            return 1
    else:
        print_error("Some optimizations failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

