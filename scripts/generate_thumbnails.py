#!/usr/bin/env python3
"""
Video Thumbnail Generator
==========================

Generate lightweight thumbnail images from videos to improve initial page load.
This is a CRITICAL optimization for reducing bandwidth usage.

Instead of loading full videos initially, show thumbnails and load videos
only when needed (on hover/click).

Usage:
    python generate_thumbnails.py [--videos-dir DIR] [--output-dir DIR] [--quality QUALITY]
    
Requirements:
    - ffmpeg must be installed: sudo apt install ffmpeg (Linux) or brew install ffmpeg (Mac)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List
import concurrent.futures


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def generate_thumbnail(video_path: Path, output_path: Path, width: int = 320, 
                      quality: int = 5, timestamp: str = "00:00:01") -> bool:
    """
    Generate a thumbnail from a video file.
    
    Args:
        video_path: Path to input video
        output_path: Path to output thumbnail image
        width: Thumbnail width in pixels (height auto-scaled)
        quality: JPEG quality (1-31, lower is better, 2-5 recommended)
        timestamp: Timestamp to extract frame from (HH:MM:SS)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run ffmpeg command
        # -ss: seek to timestamp
        # -i: input file
        # -vframes 1: extract one frame
        # -vf scale: resize keeping aspect ratio
        # -q:v: quality (2-5 is good for thumbnails)
        cmd = [
            'ffmpeg',
            '-ss', timestamp,
            '-i', str(video_path),
            '-vframes', '1',
            '-vf', f'scale={width}:-1',
            '-q:v', str(quality),
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error generating thumbnail for {video_path.name}: {e}")
        return False


def process_video(args):
    """Helper function for parallel processing."""
    video_path, output_path, width, quality, timestamp = args
    success = generate_thumbnail(video_path, output_path, width, quality, timestamp)
    return video_path.name, success, output_path


def generate_all_thumbnails(
    videos_dir: str,
    output_dir: str,
    width: int = 320,
    quality: int = 5,
    timestamp: str = "00:00:01",
    max_workers: int = 4
):
    """
    Generate thumbnails for all videos in a directory.
    
    Args:
        videos_dir: Directory containing video files
        output_dir: Directory to save thumbnails
        width: Thumbnail width
        quality: JPEG quality
        timestamp: Frame timestamp to extract
        max_workers: Number of parallel workers
    """
    videos_path = Path(videos_dir)
    output_path = Path(output_dir)
    
    if not videos_path.exists():
        print(f"Error: Videos directory not found: {videos_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("Video Thumbnail Generator")
    print("=" * 80)
    print()
    print(f"Videos directory: {videos_path}")
    print(f"Output directory: {output_path}")
    print(f"Thumbnail size: {width}px wide (auto height)")
    print(f"Quality: {quality} (1-31 scale, lower is better)")
    print(f"Timestamp: {timestamp}")
    print(f"Parallel workers: {max_workers}")
    print()
    
    # Find all video files
    video_files = list(videos_path.glob("*.mp4"))
    video_files.extend(videos_path.glob("*.webm"))
    video_files.extend(videos_path.glob("*.avi"))
    video_files.extend(videos_path.glob("*.mov"))
    
    if not video_files:
        print("No video files found. Exiting.")
        sys.exit(1)
    
    print(f"Found {len(video_files)} video files")
    print()
    
    # Check if ffmpeg is available
    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not in PATH")
        print()
        print("Install ffmpeg:")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Prepare tasks
    tasks = []
    for video_file in video_files:
        thumbnail_name = video_file.stem + ".jpg"
        thumbnail_path = output_path / thumbnail_name
        tasks.append((video_file, thumbnail_path, width, quality, timestamp))
    
    # Process videos in parallel
    print(f"Generating thumbnails (using {max_workers} workers)...")
    print()
    
    successful = 0
    failed = 0
    skipped = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_video, task) for task in tasks]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            video_name, success, thumb_path = future.result()
            
            if success:
                successful += 1
                # Get file size
                size_kb = thumb_path.stat().st_size / 1024
                if i % 50 == 0:
                    print(f"  [{i}/{len(video_files)}] Generated {successful} thumbnails...")
            else:
                failed += 1
    
    print()
    print(f"✓ Successfully generated {successful} thumbnails")
    if failed > 0:
        print(f"✗ Failed to generate {failed} thumbnails")
    print()
    
    # Calculate statistics
    if successful > 0:
        total_thumb_size = sum(
            f.stat().st_size for f in output_path.glob("*.jpg")
        )
        avg_thumb_size = total_thumb_size / successful
        
        # Estimate original video sizes (sample first 10)
        sample_videos = video_files[:min(10, len(video_files))]
        sample_sizes = [v.stat().st_size for v in sample_videos]
        avg_video_size = sum(sample_sizes) / len(sample_sizes) if sample_sizes else 0
        
        print("=" * 80)
        print("PERFORMANCE IMPACT")
        print("=" * 80)
        print()
        print(f"Average thumbnail size: {avg_thumb_size / 1024:.2f} KB")
        print(f"Total thumbnails size: {total_thumb_size / (1024*1024):.2f} MB")
        print()
        
        if avg_video_size > 0:
            print(f"Average video size: {avg_video_size / (1024*1024):.2f} MB")
            
            # Calculate savings for initial page load (assume 20 items visible)
            initial_items = 20
            before_size = initial_items * avg_video_size
            after_size = initial_items * avg_thumb_size
            savings = before_size - after_size
            
            print()
            print(f"Initial load (first {initial_items} items):")
            print(f"  Before (videos): {before_size / (1024*1024):.2f} MB")
            print(f"  After (thumbnails): {after_size / 1024:.2f} KB")
            print(f"  Savings: {savings / (1024*1024):.2f} MB ({savings/before_size*100:.1f}% reduction)")
        
        print()
    
    # Usage instructions
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. Update your HTML/JavaScript to use thumbnails:")
    print()
    print("   <div class=\"video-card\">")
    print("     <!-- Show thumbnail by default -->")
    print("     <img src=\"thumbnails/video_name.jpg\" ")
    print("          data-video=\"videos/video_name.mp4\"")
    print("          class=\"video-thumbnail\">")
    print("   </div>")
    print()
    print("2. Load videos on demand (hover/click):")
    print()
    print("   thumbnail.addEventListener('mouseenter', () => {")
    print("     const videoUrl = thumbnail.dataset.video;")
    print("     const video = document.createElement('video');")
    print("     video.src = videoUrl;")
    print("     video.autoplay = true;")
    print("     video.loop = true;")
    print("     thumbnail.replaceWith(video);")
    print("   });")
    print()
    print("3. Deploy updated files to GitHub Pages")
    print()
    print("4. Test the performance improvement")
    print()
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate thumbnail images from video files"
    )
    parser.add_argument(
        "--videos-dir",
        type=str,
        default="docs/assets/videos",
        help="Directory containing video files (default: docs/assets/videos)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/assets/thumbnails",
        help="Directory to save thumbnails (default: docs/assets/thumbnails)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=320,
        help="Thumbnail width in pixels (default: 320)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=5,
        choices=range(1, 32),
        help="JPEG quality 1-31, lower is better (default: 5)"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default="00:00:01",
        help="Timestamp to extract frame (HH:MM:SS, default: 00:00:01)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    args = parser.parse_args()
    
    generate_all_thumbnails(
        videos_dir=args.videos_dir,
        output_dir=args.output_dir,
        width=args.width,
        quality=args.quality,
        timestamp=args.timestamp,
        max_workers=args.workers
    )


if __name__ == "__main__":
    main()

