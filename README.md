# 🤖 RoboCOIN Dataset Visualizer

A powerful web-based tool for visualizing, filtering, and downloading robotics datasets. Browse thousands of robot manipulation tasks with an intuitive interface featuring real-time video previews, advanced filtering, and batch download capabilities.

## ✨ Features

### 🎯 Core Features
- **📊 Interactive Dataset Browser** - Browse robot manipulation datasets with video previews
- **🔍 Advanced Filtering System** - Filter by scene type, robot model, end effector, actions, and objects
- **🎬 Video Previews** - Lazy-loaded MP4 videos with automatic playback
- **🛒 Cart System** - Select multiple datasets and manage downloads
- **💾 Import/Export** - Save and load dataset selections as JSON
- **📋 Download Command Generation** - Auto-generate download commands for ModelScope or HuggingFace

### 🚀 Performance Features
- **Virtual Scrolling** - Smooth browsing of thousands of datasets
- **Lazy Loading** - Videos load only when visible
- **Responsive Design** - Works on desktop and mobile devices
- **Fast Search** - Real-time search across dataset names and filters
- **Optimized Rendering** - Handles 10,000+ datasets with ease

### 🎨 User Interface
- **Three-Panel Layout**
  - Left: Filter panel with hierarchical controls
  - Center: Video grid with real-time previews
  - Right: Selection cart with download commands
- **Hover Previews** - Quick preview when hovering over cart items
- **Batch Operations** - Select all, deselect all, add to cart, remove from cart
- **Filter Finder** - Search within filter options

## 🌐 Live Demo

Visit the live demo: [RoboCOIN Visualizer](https://your-username.github.io/robocoin-html/)

## 📸 Screenshots

![Main Interface](docs/screenshot-main.png)
*Main interface showing the three-panel layout with filters, video grid, and cart*

## 🛠️ Installation & Usage

### Option 1: GitHub Pages (Recommended)
1. Fork this repository
2. Enable GitHub Pages in Settings → Pages
3. Select `main` branch and `/docs` folder
4. Visit `https://your-username.github.io/robocoin-html/`

### Option 2: Local Development
```bash
# Clone the repository
git clone https://github.com/your-username/robocoin-html.git
cd robocoin-html

# Serve the docs folder with any HTTP server
# Using Python 3:
python3 -m http.server 8000 --directory docs

# Or using Node.js:
npx http-server docs -p 8000

# Open http://localhost:8000 in your browser
```

### Option 3: Direct File Access
Simply open `docs/index.html` in your web browser (some features may be limited due to CORS restrictions).

## 📁 Project Structure

```
robocoin-html/
├── docs/                          # Web application root (GitHub Pages)
│   ├── index.html                 # Main HTML file
│   ├── css/
│   │   └── style.css             # All styles (1455 lines)
│   ├── js/
│   │   ├── main.js               # Main application logic
│   │   ├── app.js                # Application state and handlers
│   │   └── templates.js          # HTML template builders
│   ├── assets/
│   │   ├── dataset_info/         # YAML metadata files
│   │   │   ├── data_index.json   # Index of all datasets
│   │   │   └── *.yml             # Individual dataset metadata
│   │   └── videos/               # MP4 video files
│   │       └── *.mp4             # Preview videos
│   └── favicon.ico
├── scripts/
│   └── dataset_generator.py      # Virtual dataset generator for testing
└── README.md                      # This file
```

## 📊 Dataset Format

### YAML Metadata (`.yml`)
Each dataset has a YAML file with the following structure:

```yaml
dataset_name: unitree_g1_five_finger_hand_basket_storage_apple
dataset_uuid: 123e4567-e89b-12d3-a456-426614174000
task_descriptions:
  - Pick up apple and place in basket
scene_type:
  - kitchen
  - home
atomic_actions:
  - grasp
  - lift
  - place
objects:
  - object_name: apple
    level1: fruit
    level2: apple
    level3: null
    level4: null
    level5: null
  - object_name: basket
    level1: container
    level2: basket
    level3: null
    level4: null
    level5: null
operation_platform_height: 80.5
device_model:
  - unitree_g1
end_effector_type: five_finger_hand
```

### Video Files (`.mp4`)
- Filename matches YAML file: `{dataset_name}.mp4`
- H.264 codec for maximum browser compatibility
- Recommended size: 100-500 KB per video
- Typical duration: 1-3 seconds

### Data Index (`data_index.json`)
```json
[
  "dataset_name_1.yml",
  "dataset_name_2.yml",
  ...
]
```

## 🔧 Configuration

### CSS Variables
The application uses CSS variables for easy customization. Edit `docs/css/style.css`:

```css
:root {
  /* Layout */
  --content-padding: 12px;
  
  /* Grid */
  --grid-min-card-width: 180px;
  --grid-card-height: 250px;
  --grid-gap: 16px;
  --grid-columns: 4;
  
  /* Selection Panel */
  --selection-item-height: 45px;
  
  /* Performance */
  --loading-batch-size: 150;
  --grid-buffer-rows: 2;
  --selection-buffer-items: 20;
  
  /* Timing */
  --hover-delay: 500ms;
  --resize-debounce: 200ms;
  --transition-duration: 200ms;
}
```

### JavaScript Configuration
Modify paths in `docs/js/app.js`:

```javascript
paths: {
  assetsRoot: './assets',
  get datasetInfo() {
    return `${this.assetsRoot}/dataset_info`;
  },
  get videos() {
    return `${this.assetsRoot}/videos`;
  }
}
```

## 🧪 Generate Test Datasets

Use the included Python script to generate virtual datasets for testing:

```bash
python3 scripts/dataset_generator.py
```

**Interactive Options:**
- Number of datasets (1-100,000)
- Robot types
- End effector types
- Scene types
- Object categories
- Object hierarchy depth (1-5 levels)
- Target video size (KB)

**Example:**
```bash
# Generate 2000 test datasets
# Output to docs/assets/
# Videos: ~100KB each
# With 3-level object hierarchy
```

The generator creates:
- YAML metadata files with realistic robot task descriptions
- MP4 video files with animated frames
- `data_index.json` index file

## 📦 Download Integration

### ModelScope
```bash
python -m robotcoin.datasets.download --hub modelscope --ds_lists \
  dataset_name_1 \
  dataset_name_2 \
  dataset_name_3
```

### HuggingFace
```bash
python -m robotcoin.datasets.download --hub huggingface --ds_lists \
  dataset_name_1 \
  dataset_name_2 \
  dataset_name_3
```

## 🎯 How to Use

### 1. Filter Datasets
- **Search Box**: Type to filter by dataset name
- **Filter Groups**: Click checkboxes to filter by:
  - Scene type (kitchen, office, warehouse, etc.)
  - Robot model (unitree_g1, boston_spot, etc.)
  - End effector (five_finger_hand, two_finger_gripper, etc.)
  - Actions (grasp, place, pick, push, etc.)
  - Objects (hierarchical categories)

### 2. Browse Videos
- Videos auto-play when scrolling into view
- Click any video card to select/deselect
- Hover over cards for detailed information
- Use toolbar buttons for batch operations:
  - ✅ Select All
  - ❌ Deselect All
  - 🔄 Reset Filters

### 3. Manage Cart
- Click **🛒 Add to Cart** to add selected items
- Click **🗑️ Remove from Cart** to remove selected items
- Click **🔄 Clear Cart** to empty the cart
- Items in cart show a success badge (✓) on video cards

### 4. Export & Download
- **📋 Import cart from .json**: Load previously saved selections
- **📤 Export cart to .json**: Save current cart for later
- **📋 Copy & 'Checkout' ⬇️**: Copy download command to clipboard
- Switch between ModelScope and HuggingFace hubs

## 🧩 Advanced Features

### Filter Finder
Search within filter options:
1. Click the filter search box
2. Type to search filter labels
3. Use ↑/↓ arrows to navigate matches
4. Press Enter to jump to next match
5. Press Esc to clear search

### Hierarchical Object Filters
Object categories are organized hierarchically:
- **Level 1**: Top category (e.g., "fruit")
- **Level 2**: Subcategory (e.g., "apple")
- **Level 3-5**: Additional hierarchy levels

Features:
- Click "All" to select/deselect entire categories
- Expand/collapse using ▶/▼ icons
- Auto-collapse when navigating

### Virtual Scrolling
Both the video grid and cart use virtual scrolling:
- Only visible items are rendered in DOM
- Smooth scrolling with thousands of items
- Configurable buffer zones for smooth experience

## 🔒 Browser Compatibility

**Supported Browsers:**
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Required Features:**
- ES6 Modules
- Intersection Observer API
- CSS Grid
- CSS Custom Properties
- Fetch API

## 🐛 Troubleshooting

### Videos not loading
- Check browser console for CORS errors
- Ensure you're serving via HTTP (not `file://`)
- Verify video files exist in `docs/assets/videos/`

### Slow performance
- Reduce `--loading-batch-size` in CSS
- Increase `--grid-buffer-rows` for smoother scrolling
- Check if browser has hardware acceleration enabled

### Filters not working
- Verify YAML metadata files are properly formatted
- Check that `data_index.json` lists all datasets
- Clear browser cache and reload

## 📈 Performance Optimization

The application is optimized for large datasets:

| Datasets | Load Time | Memory Usage | Smoothness |
|----------|-----------|--------------|------------|
| 100      | < 1s      | ~50 MB       | 60 FPS     |
| 1,000    | ~2s       | ~100 MB      | 60 FPS     |
| 10,000   | ~10s      | ~300 MB      | 60 FPS     |
| 20,000   | ~20s      | ~500 MB      | 55+ FPS    |

**Optimization Techniques:**
- Batch loading of metadata (150 files per batch)
- Virtual scrolling (only render visible items)
- Intersection Observer for lazy video loading
- RequestAnimationFrame for smooth updates
- Debounced search and resize handlers
- Cached DOM queries and sorted arrays
- Event delegation (no memory leaks)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/your-username/robocoin-html.git
cd robocoin-html

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and test locally
python3 -m http.server 8000 --directory docs

# Commit and push
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name

# Create a Pull Request
```

### Code Style
- Use ES6+ JavaScript features
- Follow existing code structure
- Comment complex logic
- Test with multiple dataset sizes
- Ensure responsive design works

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with vanilla JavaScript (no framework dependencies)
- Bootstrap for UI components
- js-yaml for YAML parsing
- Font Awesome icons (via Unicode)

## 📮 Contact

- **Project**: [github.com/your-username/robocoin-html](https://github.com/your-username/robocoin-html)
- **Issues**: [github.com/your-username/robocoin-html/issues](https://github.com/your-username/robocoin-html/issues)

---

**Made with ❤️ for the robotics community**

