# Performance Diagnostics Script

This directory contains tools for diagnosing and optimizing the performance of the RoboCOIN Dataset Visualizer.

## Performance Diagnostics Tool

### Overview

The `performance_diagnostics.py` script analyzes your GitHub Pages deployment to identify performance bottlenecks and provide actionable optimization recommendations.

### Why Performance Matters

When running locally, your application loads files from disk (very fast). On GitHub Pages:
- Each file requires a separate HTTP request over the internet
- Network latency affects every request
- GitHub Pages has connection limits
- Users may have slower connections than your development environment

### Quick Start

```bash
# Install dependencies (if needed)
pip install pyyaml  # Optional but recommended

# Run diagnostics from project root
python scripts/performance_diagnostics.py

# Or run with custom paths
python scripts/performance_diagnostics.py --docs-dir ./docs --output my_report.txt
```

### What It Analyzes

The script performs comprehensive analysis of:

1. **File Structure** - Counts and categorizes all assets
2. **Asset Sizes** - Analyzes total and average file sizes
3. **YAML Complexity** - Examines metadata structure
4. **Network Requests** - Estimates HTTP request patterns
5. **Initial Load** - Calculates data transfer requirements
6. **Caching Strategy** - Evaluates caching opportunities
7. **Recommendations** - Generates prioritized optimization suggestions

### Output

The script generates two files:

1. **performance_diagnostics_report.txt** - Human-readable report with:
   - Executive summary
   - Identified bottlenecks
   - Prioritized recommendations
   - Quick wins section

2. **performance_diagnostics_results.json** - Machine-readable detailed data

### Sample Output

```
================================================================================
RoboCOIN Performance Diagnostics
================================================================================

[1/7] Analyzing file system structure...
    ✓ Found 2000 dataset metadata files
    ✓ Found 2000 video files
    ✓ Found 3 JavaScript files
    ✓ Found 1 CSS files

[2/7] Analyzing asset sizes...
    ✓ Dataset metadata: 5.23 MB (2000 files)
    ✓ Videos: 1250.45 MB (2000 files)
    ✓ JavaScript: 65.3 KB (3 files)
    ✓ CSS: 42.1 KB (1 files)

...
```

### Common Issues Detected

#### Critical Issues

1. **Too Many HTTP Requests**
   - Problem: 2000+ individual YAML files require separate requests
   - Impact: Severe initial load delay on GitHub Pages
   - Solution: Consolidate into single JSON bundle

2. **Large Video Files**
   - Problem: Videos dominate bandwidth usage
   - Impact: Slow page loading, poor mobile experience
   - Solution: Use thumbnails, optimize encoding, lazy load

3. **No Caching Strategy**
   - Problem: No service worker or advanced caching
   - Impact: Repeat visitors reload everything
   - Solution: Implement service worker and IndexedDB

### Recommended Optimizations (Priority Order)

#### Priority 1: Consolidate Metadata Files

**Problem**: Loading 2000+ individual YAML files
**Solution**: Create a build script to merge them

```bash
# Example build script
python scripts/consolidate_metadata.py
```

This reduces 2000+ HTTP requests to just 1, providing ~90% improvement in initial load time.

#### Priority 2: Generate Video Thumbnails

**Problem**: Full videos load even when not needed
**Solution**: Generate lightweight thumbnail images

```bash
# Example using ffmpeg
for video in docs/assets/videos/*.mp4; do
    ffmpeg -i "$video" -ss 00:00:01 -vframes 1 -vf "scale=320:-1" "${video%.mp4}.jpg"
done
```

#### Priority 3: Implement Service Worker

**Problem**: No client-side caching
**Solution**: Add a service worker

```javascript
// docs/sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('v1').then((cache) => {
      return cache.addAll([
        '/js/app.js',
        '/js/main.js',
        '/css/style.css',
        '/assets/dataset_info/consolidated.json'
      ]);
    })
  );
});
```

#### Priority 4: Enable Compression

Ensure all text assets are gzip/brotli compressed. GitHub Pages does this automatically, but verify:

```bash
# Check if gzip is enabled
curl -H "Accept-Encoding: gzip" -I https://your-site.github.io/assets/dataset_info/data_index.json
```

### Performance Metrics to Track

After implementing optimizations, measure:

1. **Time to First Byte (TTFB)** - Should be < 500ms
2. **First Contentful Paint (FCP)** - Should be < 2s
3. **Time to Interactive (TTI)** - Should be < 5s
4. **Total Blocking Time (TBT)** - Should be < 300ms
5. **Cumulative Layout Shift (CLS)** - Should be < 0.1

Use tools like:
- Chrome DevTools (Network & Performance tabs)
- Lighthouse (built into Chrome)
- WebPageTest.org
- GTmetrix

### Testing Optimization Impact

1. **Before Optimization**
   ```bash
   # Run diagnostics
   python scripts/performance_diagnostics.py
   
   # Note the metrics
   # - Initial load size: X MB
   # - Initial requests: Y
   ```

2. **Implement Optimization**
   ```bash
   # Example: Consolidate metadata
   python scripts/consolidate_metadata.py
   ```

3. **After Optimization**
   ```bash
   # Run diagnostics again
   python scripts/performance_diagnostics.py
   
   # Compare metrics
   # - Initial load size: reduced by Z%
   # - Initial requests: reduced by W
   ```

### GitHub Pages Limitations

Be aware of GitHub Pages constraints:
- Max 1GB repository size
- Max 100GB bandwidth per month
- No server-side processing
- No custom headers (limited caching control)
- Connection pooling limits

### Advanced Optimizations

For further improvements:

1. **Use External CDN for Videos**
   - Host videos on Cloudflare R2, AWS S3, or similar
   - Serves with better compression and edge caching

2. **Implement Virtual Scrolling**
   - Already implemented! Good job
   - Ensures only visible items render

3. **Code Splitting**
   - Split JavaScript into chunks
   - Load features on-demand

4. **Pre-rendering**
   - Generate static HTML for filter options
   - Calculate statistics at build time

### Troubleshooting

#### Script fails to find files
```bash
# Make sure you're in the project root
cd /path/to/robocoin-html
python scripts/performance_diagnostics.py --docs-dir ./docs
```

#### PyYAML not available
```bash
pip install pyyaml
# Or run without it (limited YAML analysis)
python scripts/performance_diagnostics.py
```

#### Permission denied
```bash
chmod +x scripts/performance_diagnostics.py
./scripts/performance_diagnostics.py
```

### Contributing

To improve the diagnostics script:
1. Add new analysis functions
2. Enhance recommendations
3. Add automated fix scripts
4. Improve report formatting

### References

- [Web Performance Optimization](https://web.dev/performance/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Web Vitals](https://web.dev/vitals/)

---

## Additional Scripts

### Coming Soon

- `consolidate_metadata.py` - Merge YAML files into optimized JSON
- `generate_thumbnails.py` - Create video thumbnails
- `setup_service_worker.py` - Auto-generate service worker
- `analyze_bundle_size.py` - Analyze JavaScript bundle sizes
- `optimize_images.py` - Compress and optimize images

---

**Need Help?**

For questions or issues with the performance diagnostics:
1. Check the generated report for specific guidance
2. Review the recommendations section
3. Start with "Quick Wins" for immediate improvements
4. Measure impact after each change

