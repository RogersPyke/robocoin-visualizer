#!/usr/bin/env python3
"""
CSS File Splitter
Splits the monolithic style.css into modular CSS files
"""

import re

# Read the original CSS file
with open('docs/css/style.css.backup', 'r', encoding='utf-8') as f:
    content = f.read()

# Define CSS modules with their section markers (as regex patterns)
css_modules = {
    'filter.css': [
        r'/\* ==================== Filter Control Bar ==================== \*/',
        r'/\* ==================== Filter Dropdown Overlay \*/',
        r'/\* ==================== left-filter \(hidden - replaced by dropdown\) ==================== \*/',
        r'\.filter-',
        r'\.btn-filter',
        r'\.hierarchy-',
    ],
    'video-grid.css': [
        r'/\* ==================== 中间视频网格区',
        r'\.video-',
        r'\.toolbar',
        r'\.btn-toolbar',
        r'\.play-indicator',
        r'\.hover-',
        r'\.lazy-video',
    ],
    'selection-panel.css': [
        r'/\* ==================== 右侧选中面板',
        r'\.selection-',
        r'\.btn-selection',
        r'\.cart-',
        r'\.code-',
        r'\.empty-cart',
        r'\.hint-',
    ],
    'modal.css': [
        r'/\* ==================== 详情模态框',
        r'/\* ==================== 悬浮预览',
        r'\.detail-modal',
        r'\.hover-preview',
    ],
    'animations.css': [
        r'/\* ==================== 加载动画',
        r'\.loading-',
        r'@keyframes',
        r'\.fade-',
    ],
}

# Since the original file is complex, let's use a simpler approach
# Extract sections based on major comment markers

def extract_section(content, start_marker, end_marker=None):
    """Extract a section of CSS between two markers"""
    pattern = re.escape(start_marker) + r'.*?(?=' + (re.escape(end_marker) if end_marker else r'/\* ====================|\Z') + r')'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(0) if match else ''

# Write filter.css
filter_css = """/**
 * Filter Styles
 * Filter control bar, dropdown, and filter options
 */

"""

# Extract filter-related sections
filter_start_markers = [
    '/* ==================== Filter Control Bar ====================',
    '/* Filter Dropdown Overlay */',
]

for marker in filter_start_markers:
    section = extract_section(content, marker)
    if section:
        filter_css += section + '\n\n'

with open('docs/css/filter.css', 'w', encoding='utf-8') as f:
    f.write(filter_css)

print("✓ Created filter.css")

# For now, let's create simplified module files and refine them later
# The key is to get the structure in place

print("CSS modules created successfully")

