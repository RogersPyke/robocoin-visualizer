# RoboCOIN Dataset Visualizer

HTML interface for RoboCOIN dataset visualization and download.

## Standard Asset Structure

The application follows a standardized directory structure for dataset assets:

```
docs/
├── assets/
│   ├── info/               # JSON index files
│   │   ├── data_index.json              # List of all dataset names
│   │   └── consolidated_datasets.json   # Full consolidated dataset metadata
│   │
│   ├── dataset_info/       # YAML metadata files (one per dataset)
│   │   ├── *.yml           # Dataset metadata in YAML format
│   │   └── *.yaml          # Alternative YAML extension
│   │
│   └── videos/             # MP4 video demonstrations
│       └── *.mp4           # Video files named by dataset path
│
├── css/
├── js/
├── index.html
└── README.md
```

## Dataset Metadata Format

Each dataset has a corresponding YAML file in `assets/dataset_info/` with this structure:

```yaml
dataset_name: [task_name]
dataset_uuid: [optional UUID]
task_descriptions:
  - [description text]
scene_type:
  - [location category]
  - [specific location]
atomic_actions:
  - [action verbs like grasp, pick, place, wipe]
objects:
  - object_name: [name]
    level1: [category]
    level2: [subcategory]
    level3: [optional]
    level4: [optional]
    level5: [optional]
operation_platform_height: [height in cm]
device_model:
  - [robot model name]
end_effector_type: [gripper type]
```

## Path Configuration

The application uses the following path structure (defined in `js/app.js`):

- **Assets Root**: `./assets`
- **Info Files**: `./assets/info` (JSON indexes)
- **Dataset Info**: `./assets/dataset_info` (YAML metadata)
- **Videos**: `./assets/videos` (MP4 files)

## Usage

1. Open `index.html` in a web browser
2. Browse and filter datasets using the left panel
3. Select datasets and add them to cart
4. Generate download commands from the cart
