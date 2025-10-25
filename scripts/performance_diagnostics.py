#!/usr/bin/env python3
"""
Performance Diagnostics Script for RoboCOIN Dataset Visualizer
===============================================================

This script analyzes the performance bottlenecks of the application
when deployed on GitHub Pages and proposes optimization strategies.

Usage:
    python performance_diagnostics.py [--docs-dir DOCS_DIR] [--output REPORT_FILE]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import time
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not installed. YAML parsing will be limited.")
    yaml = None


class PerformanceDiagnostics:
    """Main diagnostics class for analyzing performance bottlenecks."""
    
    def __init__(self, docs_dir: str):
        self.docs_dir = Path(docs_dir)
        self.dataset_info_dir = self.docs_dir / "assets" / "dataset_info"
        self.videos_dir = self.docs_dir / "assets" / "videos"
        self.results = {
            "summary": {},
            "bottlenecks": [],
            "recommendations": [],
            "detailed_analysis": {}
        }
        
    def run_full_diagnostics(self) -> Dict:
        """Run all diagnostic tests."""
        print("=" * 80)
        print("RoboCOIN Performance Diagnostics")
        print("=" * 80)
        print()
        
        # 1. File System Analysis
        print("[1/7] Analyzing file system structure...")
        self.analyze_file_structure()
        
        # 2. Asset Size Analysis
        print("[2/7] Analyzing asset sizes...")
        self.analyze_asset_sizes()
        
        # 3. YAML Content Analysis
        print("[3/7] Analyzing YAML content complexity...")
        self.analyze_yaml_complexity()
        
        # 4. Network Request Estimation
        print("[4/7] Estimating network request patterns...")
        self.estimate_network_requests()
        
        # 5. Initial Load Analysis
        print("[5/7] Analyzing initial load requirements...")
        self.analyze_initial_load()
        
        # 6. Caching Strategy Analysis
        print("[6/7] Analyzing caching strategies...")
        self.analyze_caching_potential()
        
        # 7. Generate Recommendations
        print("[7/7] Generating optimization recommendations...")
        self.generate_recommendations()
        
        print()
        print("Diagnostics complete!")
        print()
        
        return self.results
    
    def analyze_file_structure(self):
        """Analyze the file structure and count assets."""
        print("  - Counting dataset files...")
        
        # Count YAML files
        yml_files = list(self.dataset_info_dir.glob("*.yml"))
        yaml_files = list(self.dataset_info_dir.glob("*.yaml"))
        json_files = list(self.dataset_info_dir.glob("*.json"))
        total_dataset_files = len(yml_files) + len(yaml_files)
        
        # Count video files
        video_files = list(self.videos_dir.glob("*.mp4"))
        
        # Count other assets
        js_files = list(self.docs_dir.glob("js/*.js"))
        css_files = list(self.docs_dir.glob("css/*.css"))
        
        structure = {
            "yml_files": len(yml_files),
            "yaml_files": len(yaml_files),
            "json_files": len(json_files),
            "total_dataset_files": total_dataset_files,
            "video_files": len(video_files),
            "js_files": len(js_files),
            "css_files": len(css_files)
        }
        
        self.results["detailed_analysis"]["file_structure"] = structure
        
        print(f"    ✓ Found {total_dataset_files} dataset metadata files")
        print(f"    ✓ Found {len(video_files)} video files")
        print(f"    ✓ Found {len(js_files)} JavaScript files")
        print(f"    ✓ Found {len(css_files)} CSS files")
        
        # Identify bottleneck
        if total_dataset_files > 1000:
            self.results["bottlenecks"].append({
                "category": "File Count",
                "severity": "HIGH",
                "issue": f"Large number of dataset files ({total_dataset_files})",
                "impact": "Each file requires a separate HTTP request on GitHub Pages, causing significant network overhead"
            })
    
    def analyze_asset_sizes(self):
        """Analyze the sizes of various assets."""
        print("  - Calculating asset sizes...")
        
        sizes = {
            "dataset_metadata": {"count": 0, "total_bytes": 0, "sizes": []},
            "videos": {"count": 0, "total_bytes": 0, "sizes": []},
            "js": {"count": 0, "total_bytes": 0, "sizes": []},
            "css": {"count": 0, "total_bytes": 0, "sizes": []},
            "json_index": {"count": 0, "total_bytes": 0, "sizes": []}
        }
        
        # Analyze YAML files
        for yml_file in self.dataset_info_dir.glob("*.yml"):
            size = yml_file.stat().st_size
            sizes["dataset_metadata"]["count"] += 1
            sizes["dataset_metadata"]["total_bytes"] += size
            sizes["dataset_metadata"]["sizes"].append(size)
        
        # Analyze JSON files
        for json_file in self.dataset_info_dir.glob("*.json"):
            size = json_file.stat().st_size
            sizes["json_index"]["count"] += 1
            sizes["json_index"]["total_bytes"] += size
            sizes["json_index"]["sizes"].append(size)
        
        # Analyze videos
        for video_file in self.videos_dir.glob("*.mp4"):
            size = video_file.stat().st_size
            sizes["videos"]["count"] += 1
            sizes["videos"]["total_bytes"] += size
            sizes["videos"]["sizes"].append(size)
        
        # Analyze JS files
        for js_file in self.docs_dir.glob("js/*.js"):
            size = js_file.stat().st_size
            sizes["js"]["count"] += 1
            sizes["js"]["total_bytes"] += size
            sizes["js"]["sizes"].append(size)
        
        # Analyze CSS files
        for css_file in self.docs_dir.glob("css/*.css"):
            size = css_file.stat().st_size
            sizes["css"]["count"] += 1
            sizes["css"]["total_bytes"] += size
            sizes["css"]["sizes"].append(size)
        
        # Calculate statistics
        for category, data in sizes.items():
            if data["sizes"]:
                data["min"] = min(data["sizes"])
                data["max"] = max(data["sizes"])
                data["avg"] = data["total_bytes"] / len(data["sizes"])
                del data["sizes"]  # Remove raw data to keep output clean
        
        self.results["detailed_analysis"]["asset_sizes"] = sizes
        
        # Print summary
        total_metadata_mb = sizes["dataset_metadata"]["total_bytes"] / (1024 * 1024)
        total_videos_mb = sizes["videos"]["total_bytes"] / (1024 * 1024)
        total_js_kb = sizes["js"]["total_bytes"] / 1024
        total_css_kb = sizes["css"]["total_bytes"] / 1024
        
        print(f"    ✓ Dataset metadata: {total_metadata_mb:.2f} MB ({sizes['dataset_metadata']['count']} files)")
        print(f"    ✓ Videos: {total_videos_mb:.2f} MB ({sizes['videos']['count']} files)")
        print(f"    ✓ JavaScript: {total_js_kb:.2f} KB ({sizes['js']['count']} files)")
        print(f"    ✓ CSS: {total_css_kb:.2f} KB ({sizes['css']['count']} files)")
        
        # Identify bottlenecks
        if total_videos_mb > 500:
            self.results["bottlenecks"].append({
                "category": "Video Size",
                "severity": "CRITICAL",
                "issue": f"Large total video size ({total_videos_mb:.2f} MB)",
                "impact": "Videos are the primary bandwidth bottleneck, especially on slower connections"
            })
        
        if total_metadata_mb > 10:
            self.results["bottlenecks"].append({
                "category": "Metadata Size",
                "severity": "HIGH",
                "issue": f"Large total metadata size ({total_metadata_mb:.2f} MB)",
                "impact": "Loading all metadata files creates significant initial load time"
            })
        
        # Check individual file sizes
        if sizes["videos"]["avg"] > 1024 * 1024 * 2:  # 2MB
            avg_mb = sizes["videos"]["avg"] / (1024 * 1024)
            self.results["bottlenecks"].append({
                "category": "Video Size",
                "severity": "MEDIUM",
                "issue": f"Average video size is large ({avg_mb:.2f} MB)",
                "impact": "Large individual videos slow down lazy loading"
            })
    
    def analyze_yaml_complexity(self):
        """Analyze YAML file complexity and parsing requirements."""
        print("  - Analyzing YAML complexity...")
        
        if not yaml:
            print("    ! Skipping (PyYAML not available)")
            return
        
        sample_size = min(50, len(list(self.dataset_info_dir.glob("*.yml"))))
        yml_files = list(self.dataset_info_dir.glob("*.yml"))[:sample_size]
        
        complexity = {
            "sample_size": sample_size,
            "avg_keys": 0,
            "avg_nested_depth": 0,
            "avg_objects": 0,
            "common_fields": defaultdict(int)
        }
        
        total_keys = 0
        total_objects = 0
        
        for yml_file in yml_files:
            try:
                with open(yml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if isinstance(data, dict):
                    total_keys += len(data.keys())
                    for key in data.keys():
                        complexity["common_fields"][key] += 1
                    
                    if "objects" in data and isinstance(data["objects"], list):
                        total_objects += len(data["objects"])
            except Exception as e:
                print(f"    ! Error parsing {yml_file.name}: {e}")
        
        if sample_size > 0:
            complexity["avg_keys"] = total_keys / sample_size
            complexity["avg_objects"] = total_objects / sample_size
        
        # Convert defaultdict to regular dict for JSON serialization
        complexity["common_fields"] = dict(complexity["common_fields"])
        
        self.results["detailed_analysis"]["yaml_complexity"] = complexity
        
        print(f"    ✓ Analyzed {sample_size} YAML files")
        print(f"    ✓ Average keys per file: {complexity['avg_keys']:.1f}")
        print(f"    ✓ Average objects per file: {complexity['avg_objects']:.1f}")
    
    def estimate_network_requests(self):
        """Estimate network request patterns."""
        print("  - Estimating network requests...")
        
        file_structure = self.results["detailed_analysis"]["file_structure"]
        
        # Initial load requests
        initial_requests = {
            "html": 1,
            "css": file_structure["css_files"],
            "js": file_structure["js_files"],
            "json_index": file_structure["json_files"],
            "favicon": 1,
            "fonts": 0  # Might load external fonts
        }
        
        # Batch loading (as per app.js line 161)
        batch_size = 150
        dataset_files = file_structure["total_dataset_files"]
        num_batches = (dataset_files + batch_size - 1) // batch_size
        
        # Video loading (lazy loaded via IntersectionObserver)
        # Estimate ~20 videos visible initially
        initial_visible_videos = min(20, file_structure["video_files"])
        
        request_pattern = {
            "initial_page_load": sum(initial_requests.values()),
            "first_batch_yml": batch_size,
            "total_batches": num_batches,
            "total_yml_requests": dataset_files,
            "initial_videos": initial_visible_videos,
            "total_possible_video_requests": file_structure["video_files"]
        }
        
        total_initial = (
            request_pattern["initial_page_load"] +
            request_pattern["first_batch_yml"] +
            request_pattern["initial_videos"]
        )
        
        self.results["detailed_analysis"]["network_requests"] = request_pattern
        self.results["summary"]["estimated_initial_requests"] = total_initial
        
        print(f"    ✓ Initial page load: {request_pattern['initial_page_load']} requests")
        print(f"    ✓ First data batch: {request_pattern['first_batch_yml']} YML files")
        print(f"    ✓ Total batches: {request_pattern['total_batches']}")
        print(f"    ✓ Estimated total initial requests: {total_initial}")
        
        # Identify bottleneck
        if total_initial > 100:
            self.results["bottlenecks"].append({
                "category": "Network Requests",
                "severity": "CRITICAL",
                "issue": f"Very high number of initial requests ({total_initial})",
                "impact": "GitHub Pages has connection limits, causing request queuing and slow initial load"
            })
        
        if request_pattern["total_yml_requests"] > 500:
            self.results["bottlenecks"].append({
                "category": "Sequential Loading",
                "severity": "HIGH",
                "issue": f"Sequential loading of {request_pattern['total_yml_requests']} YAML files",
                "impact": "Even with batching, this creates significant cumulative latency"
            })
    
    def analyze_initial_load(self):
        """Analyze initial load requirements."""
        print("  - Analyzing initial load sequence...")
        
        sizes = self.results["detailed_analysis"]["asset_sizes"]
        requests = self.results["detailed_analysis"]["network_requests"]
        
        # Estimate initial load data transfer
        first_batch = requests["first_batch_yml"]
        avg_yml_size = sizes["dataset_metadata"].get("avg", 0)
        first_batch_mb = (first_batch * avg_yml_size) / (1024 * 1024)
        
        initial_videos = requests["initial_videos"]
        avg_video_size = sizes["videos"].get("avg", 0)
        initial_videos_mb = (initial_videos * avg_video_size) / (1024 * 1024)
        
        js_mb = sizes["js"]["total_bytes"] / (1024 * 1024)
        css_mb = sizes["css"]["total_bytes"] / (1024 * 1024)
        
        total_initial_mb = first_batch_mb + initial_videos_mb + js_mb + css_mb
        
        initial_load = {
            "first_batch_metadata_mb": round(first_batch_mb, 2),
            "initial_videos_mb": round(initial_videos_mb, 2),
            "javascript_mb": round(js_mb, 2),
            "css_mb": round(css_mb, 2),
            "total_initial_mb": round(total_initial_mb, 2)
        }
        
        # Estimate load times at different connection speeds
        speeds = {
            "Fast 3G (1.6 Mbps)": 1.6 / 8,  # MB/s
            "4G (10 Mbps)": 10 / 8,
            "WiFi (50 Mbps)": 50 / 8
        }
        
        load_times = {}
        for name, speed_mbs in speeds.items():
            time_seconds = total_initial_mb / speed_mbs
            load_times[name] = round(time_seconds, 1)
        
        initial_load["estimated_load_times"] = load_times
        
        self.results["detailed_analysis"]["initial_load"] = initial_load
        self.results["summary"]["initial_load_size_mb"] = total_initial_mb
        
        print(f"    ✓ First batch metadata: {first_batch_mb:.2f} MB")
        print(f"    ✓ Initial videos: {initial_videos_mb:.2f} MB")
        print(f"    ✓ Total initial load: {total_initial_mb:.2f} MB")
        print(f"    ✓ Estimated load time (4G): {load_times['4G (10 Mbps)']}s")
        
        # Identify bottleneck
        if total_initial_mb > 50:
            self.results["bottlenecks"].append({
                "category": "Initial Load Size",
                "severity": "CRITICAL",
                "issue": f"Very large initial load ({total_initial_mb:.1f} MB)",
                "impact": "Users experience long wait times before interaction is possible"
            })
    
    def analyze_caching_potential(self):
        """Analyze caching strategies and potential improvements."""
        print("  - Analyzing caching strategies...")
        
        # Check for cache control files
        has_service_worker = (self.docs_dir / "sw.js").exists()
        has_manifest = (self.docs_dir / "manifest.json").exists()
        
        caching = {
            "service_worker": has_service_worker,
            "manifest": has_manifest,
            "github_pages_caching": "default",  # GitHub Pages has default caching
            "cache_potential": {}
        }
        
        # Analyze what could be cached
        sizes = self.results["detailed_analysis"]["asset_sizes"]
        
        caching["cache_potential"] = {
            "static_assets_mb": round(
                (sizes["js"]["total_bytes"] + sizes["css"]["total_bytes"]) / (1024 * 1024),
                2
            ),
            "metadata_files": sizes["dataset_metadata"]["count"],
            "videos_cacheable": False  # Too large to cache all
        }
        
        self.results["detailed_analysis"]["caching"] = caching
        
        print(f"    ✓ Service Worker: {'Yes' if has_service_worker else 'No'}")
        print(f"    ✓ Static assets cacheable: {caching['cache_potential']['static_assets_mb']} MB")
        
        # Identify opportunities
        if not has_service_worker:
            self.results["bottlenecks"].append({
                "category": "Caching",
                "severity": "MEDIUM",
                "issue": "No service worker for advanced caching",
                "impact": "Repeated visits require re-downloading assets"
            })
    
    def generate_recommendations(self):
        """Generate optimization recommendations based on analysis."""
        print("  - Generating recommendations...")
        
        recommendations = []
        
        # Priority 1: Reduce number of HTTP requests
        if any(b["category"] == "Network Requests" for b in self.results["bottlenecks"]):
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Data Architecture",
                "title": "Consolidate YAML files into a single JSON bundle",
                "description": (
                    "Instead of loading 2000+ individual YAML files, consolidate all metadata "
                    "into a single JSON file. This reduces 2000+ HTTP requests to just 1."
                ),
                "implementation": [
                    "Create a build script to merge all YAML files into one JSON",
                    "Compress the JSON (gzip compression reduces size by ~70%)",
                    "Load single JSON file on app initialization",
                    "Parse all data in memory instead of sequential fetching"
                ],
                "expected_impact": "90% reduction in initial load time",
                "effort": "Medium (requires build step)"
            })
        
        # Priority 2: Implement pagination/virtual loading
        recommendations.append({
            "priority": "HIGH",
            "category": "Data Loading",
            "title": "Implement true server-side pagination or split bundles",
            "description": (
                "Even with consolidated JSON, loading 2000 datasets at once is heavy. "
                "Split into multiple smaller bundles or implement on-demand loading."
            ),
            "implementation": [
                "Split data into chunks (e.g., 10 files of 200 datasets each)",
                "Load first chunk immediately, others on-demand",
                "Implement filter-aware lazy loading",
                "Add loading indicators for async chunks"
            ],
            "expected_impact": "80% reduction in initial load size",
            "effort": "Medium"
        })
        
        # Priority 3: Video optimization
        if any(b["category"] == "Video Size" for b in self.results["bottlenecks"]):
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Video Optimization",
                "title": "Optimize video files and implement better lazy loading",
                "description": (
                    "Videos are the largest assets. Optimize encoding and implement "
                    "progressive loading strategies."
                ),
                "implementation": [
                    "Re-encode videos with better compression (H.264 high profile)",
                    "Generate thumbnail images (much smaller than videos)",
                    "Show thumbnails by default, load videos only on hover/click",
                    "Consider creating multiple quality versions",
                    "Use video streaming with range requests",
                    "Implement aggressive video unloading when scrolled out of view"
                ],
                "expected_impact": "70% reduction in bandwidth usage",
                "effort": "High (requires video processing)"
            })
        
        # Priority 4: CDN and caching
        recommendations.append({
            "priority": "HIGH",
            "category": "Infrastructure",
            "title": "Leverage CDN and implement aggressive caching",
            "description": (
                "GitHub Pages serves files, but lacks advanced CDN features. "
                "Implement client-side caching strategies."
            ),
            "implementation": [
                "Add service worker for offline caching",
                "Implement IndexedDB for storing dataset metadata",
                "Add cache headers to HTML (via meta tags)",
                "Consider using a separate CDN for videos (e.g., Cloudflare R2)",
                "Implement versioned URLs for cache busting"
            ],
            "expected_impact": "Near-instant load for returning visitors",
            "effort": "Medium"
        })
        
        # Priority 5: Code splitting
        recommendations.append({
            "priority": "MEDIUM",
            "category": "JavaScript Optimization",
            "title": "Implement code splitting and minimize JavaScript",
            "description": "Split JavaScript into smaller chunks and load on-demand.",
            "implementation": [
                "Use dynamic imports for non-critical features",
                "Minify JavaScript files",
                "Remove unused dependencies (check js-yaml usage)",
                "Consider using a bundler (Webpack/Rollup) with tree-shaking",
                "Defer non-critical JavaScript"
            ],
            "expected_impact": "30% faster initial page render",
            "effort": "Low to Medium"
        })
        
        # Priority 6: Pre-generation strategy
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Build Process",
            "title": "Implement static generation for filters and indices",
            "description": (
                "Pre-calculate filters, counts, and indices at build time "
                "instead of runtime."
            ),
            "implementation": [
                "Generate filter options during build",
                "Pre-calculate dataset counts per filter",
                "Create search indices (consider Fuse.js with pre-built index)",
                "Generate dataset map/lookup tables"
            ],
            "expected_impact": "Faster filter rendering and interaction",
            "effort": "Low"
        })
        
        # Priority 7: Progressive loading UI
        recommendations.append({
            "priority": "MEDIUM",
            "category": "User Experience",
            "title": "Enhance progressive loading experience",
            "description": (
                "Make the loading process feel faster with better UX patterns."
            ),
            "implementation": [
                "Show partial results immediately (first 50 items)",
                "Implement skeleton screens instead of loading spinners",
                "Add 'Load More' button instead of auto-loading everything",
                "Show meaningful progress (e.g., 'Loaded 200/2000 datasets')",
                "Enable interaction with loaded data before everything is ready"
            ],
            "expected_impact": "Perceived performance improvement",
            "effort": "Low"
        })
        
        # Priority 8: Compression
        recommendations.append({
            "priority": "HIGH",
            "category": "Compression",
            "title": "Enable aggressive compression for all assets",
            "description": "Ensure all text assets are properly compressed.",
            "implementation": [
                "GitHub Pages serves gzip automatically, but verify it's working",
                "Consider pre-compressing assets (brotli)",
                "Check that YAML/JSON files are being compressed",
                "Minify CSS and HTML"
            ],
            "expected_impact": "50-70% reduction in transfer size for text assets",
            "effort": "Low"
        })
        
        self.results["recommendations"] = recommendations
        
        print(f"    ✓ Generated {len(recommendations)} recommendations")
    
    def generate_report(self, output_file: str = None):
        """Generate a formatted report."""
        report_lines = []
        
        # Header
        report_lines.append("=" * 80)
        report_lines.append("ROBOCOIN PERFORMANCE DIAGNOSTICS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Executive Summary
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("-" * 80)
        report_lines.append("")
        
        if "initial_load_size_mb" in self.results["summary"]:
            report_lines.append(
                f"Initial Load Size: {self.results['summary']['initial_load_size_mb']:.1f} MB"
            )
        if "estimated_initial_requests" in self.results["summary"]:
            report_lines.append(
                f"Initial HTTP Requests: {self.results['summary']['estimated_initial_requests']}"
            )
        report_lines.append("")
        
        # Bottlenecks
        report_lines.append("IDENTIFIED BOTTLENECKS")
        report_lines.append("-" * 80)
        report_lines.append("")
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_bottlenecks = sorted(
            self.results["bottlenecks"],
            key=lambda x: severity_order.get(x["severity"], 99)
        )
        
        for i, bottleneck in enumerate(sorted_bottlenecks, 1):
            report_lines.append(f"{i}. [{bottleneck['severity']}] {bottleneck['category']}")
            report_lines.append(f"   Issue: {bottleneck['issue']}")
            report_lines.append(f"   Impact: {bottleneck['impact']}")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("OPTIMIZATION RECOMMENDATIONS")
        report_lines.append("-" * 80)
        report_lines.append("")
        
        for i, rec in enumerate(self.results["recommendations"], 1):
            report_lines.append(f"{i}. [{rec['priority']}] {rec['title']}")
            report_lines.append(f"   Category: {rec['category']}")
            report_lines.append(f"   {rec['description']}")
            report_lines.append("")
            report_lines.append("   Implementation Steps:")
            for step in rec["implementation"]:
                report_lines.append(f"   - {step}")
            report_lines.append("")
            report_lines.append(f"   Expected Impact: {rec['expected_impact']}")
            report_lines.append(f"   Effort: {rec['effort']}")
            report_lines.append("")
        
        # Quick Wins
        report_lines.append("QUICK WINS (Low Effort, High Impact)")
        report_lines.append("-" * 80)
        report_lines.append("")
        
        quick_wins = [
            "1. Consolidate all YAML files into a single compressed JSON bundle",
            "2. Generate and use thumbnail images instead of loading full videos initially",
            "3. Implement service worker for caching static assets",
            "4. Minify JavaScript and CSS files",
            "5. Show first 50 results immediately while loading rest in background"
        ]
        
        for win in quick_wins:
            report_lines.append(win)
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Output
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n✓ Report saved to: {output_file}")
        
        print("\n" + report_text)
        
        return report_text
    
    def save_json_results(self, output_file: str):
        """Save detailed results as JSON."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Detailed JSON results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Diagnose performance bottlenecks in RoboCOIN Dataset Visualizer"
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default="docs",
        help="Path to docs directory (default: docs)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="performance_diagnostics_report.txt",
        help="Output report file (default: performance_diagnostics_report.txt)"
    )
    parser.add_argument(
        "--json",
        type=str,
        default="performance_diagnostics_results.json",
        help="JSON output file (default: performance_diagnostics_results.json)"
    )
    
    args = parser.parse_args()
    
    # Validate docs directory
    docs_path = Path(args.docs_dir)
    if not docs_path.exists():
        print(f"Error: Docs directory not found: {docs_path}")
        sys.exit(1)
    
    # Run diagnostics
    diagnostics = PerformanceDiagnostics(args.docs_dir)
    diagnostics.run_full_diagnostics()
    
    # Generate reports
    diagnostics.generate_report(args.output)
    diagnostics.save_json_results(args.json)
    
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("1. Review the recommendations in order of priority")
    print("2. Start with 'CRITICAL' priority items for maximum impact")
    print("3. Consider implementing the 'Quick Wins' section first")
    print("4. Measure performance improvements after each optimization")
    print("=" * 80)


if __name__ == "__main__":
    main()

