# Laser Spot Analyzer - Complete Documentation

A sophisticated Python application for detecting, analyzing, and measuring laser spots in scientific images. This tool provides interactive parameter tuning, automated threshold optimization, and manual quality review interfaces.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Installation & Setup](#installation--setup)
3. [Core Architecture](#core-architecture)
4. [Module Reference](#module-reference)
5. [Class API Documentation](#class-api-documentation)
6. [Usage Examples](#usage-examples)
7. [Workflows](#workflows)
8. [Configuration](#configuration)
9. [GUI Guide](#gui-guide)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Laser Spot Analyzer** is designed to:
- Load and process CZI microscope images
- Automatically detect laser spots (blobs) in images
- Provide interactive parameter tuning for detection optimization
- Filter and validate detected blobs
- Analyze blob statistics (diameter, distribution, etc.)
- Export results in multiple formats (CSV, JSON)

### Key Features
- **Interactive Parameter Tuning**: Real-time preview with slider controls
- **Automated Threshold Optimization**: Binary search algorithm to find optimal threshold
- **Manual Review Interface**: Click-to-select blobs with keyboard shortcuts
- **ROI Selection**: Define regions of interest for analysis
- **Material Presets**: Pre-configured settings for glass and aluminum samples
- **Statistics Computation**: Mean, standard deviation, coefficient of variation
- **GUI Application**: User-friendly PySide6-based interface

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Windows/Linux/macOS
- Git (optional, for cloning)

### Step 1: Clone Repository
```bash
git clone https://github.com/noelbenny111/laser_spot_analyzer.git
cd laser_spot_analyzer
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "from core import detection, preprocessing; print('✓ Installation successful')"
```

---

## Core Architecture

```
laser_spot_analyzer/
├── core/                          # Core processing modules
│   ├── detection.py               # Blob detection (detect_blobs)
│   ├── preprocessing.py           # Image preprocessing (preprocess)
│   ├── filtering.py               # Blob filtering (filter_blobs)
│   ├── regions.py                 # Image region splitting (split_columns)
│   ├── interaction.py             # Manual review UI (ManualReviewInterface)
│   ├── roi.py                     # ROI selection (ROI, ROISelector)
│   ├── statistics.py              # Statistical analysis (compute_statistics)
│   ├── io.py                      # File I/O (load_czi, save_csv)
│   ├── interactive_tuner.py       # Parameter tuning (InteractiveTuner)
│   ├── threshold_optimizer.py     # Threshold optimization (optimize_threshold)
│   └── __init__.py
├── gui/                           # GUI components
│   ├── main_window.py             # Main application window
│   └── __init__.py
├── config.py                      # Global configuration (presets, defaults)
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Data Flow
```
CZI Image → Preprocessing → Detection → Filtering → Statistics → Output
              ↓
        Interactive Tuner (optional)
              ↓
        Manual Review (optional)
              ↓
        Analysis Results
```

---

## Module Reference

### `core/detection.py`
Detects blobs (laser spots) in preprocessed images using contour detection.

**Function: `detect_blobs(img, params)`**
- **Parameters**:
  - `img` (np.ndarray): 8-bit preprocessed image
  - `params` (dict): Detection parameters
    - `threshold` (int): Binary threshold [0-255]
    - `morph_iter` (int): Morphological closing iterations
    - `min_diam` (float): Minimum blob diameter in pixels
    - `max_diam` (float): Maximum blob diameter in pixels

- **Returns**: List of blob dictionaries
  ```python
  {
    "center": (x, y),        # Blob center coordinates
    "diam_px": float,        # Diameter in pixels
    "ellipse": tuple or None # ((x,y), (MA,ma), angle) or None for circles
  }
  ```

- **Example**:
  ```python
  from core.detection import detect_blobs
  
  blobs = detect_blobs(preprocessed_img, {
      "threshold": 100,
      "morph_iter": 2,
      "min_diam": 5,
      "max_diam": 200
  })
  print(f"Detected {len(blobs)} blobs")
  ```

---

### `core/preprocessing.py`
Enhances images for better blob detection using CLAHE, morphological operations, and filtering.

**Function: `preprocess(img, preset)`**
- **Parameters**:
  - `img` (np.ndarray): Raw input image (any bit depth)
  - `preset` (dict): Preprocessing parameters
    - `invert` (bool): Invert colors if True
    - `clahe_clip` (float): CLAHE clipping limit [0.5-10]
    - `tophat_kernel` (int): Morphological tophat kernel size [3-80]
    - `median_kernel` (int): Median blur kernel [1-31, must be odd]

- **Returns**: 8-bit processed image (np.uint8)

- **Example**:
  ```python
  from core.preprocessing import preprocess
  from config import MATERIAL_PRESETS
  
  preset = MATERIAL_PRESETS["glass"].copy()
  processed = preprocess(raw_img, preset)
  ```

---

### `core/filtering.py`
Filters blob lists based on size and count criteria.

**Function: `filter_blobs(blobs, max_blobs)`**
- **Parameters**:
  - `blobs` (list): List of blob dictionaries
  - `max_blobs` (int): Maximum blobs to retain (keeps largest)

- **Returns**: Filtered list of blob dictionaries, sorted by diameter (descending)

- **Example**:
  ```python
  from core.filtering import filter_blobs
  
  # Keep only top 5 largest blobs
  top_blobs = filter_blobs(detected_blobs, max_blobs=5)
  ```

---

### `core/regions.py`
Splits images into vertical column regions (useful for spectrometer-style data).

**Function: `split_columns(img, deg_start, deg_end, width)`**
- **Parameters**:
  - `img` (np.ndarray): Input image
  - `deg_start` (int): Starting degree
  - `deg_end` (int): Ending degree (inclusive)
  - `width` (int): Width of each column in pixels

- **Returns**: Dictionary mapping degree values to image regions (ndarray slices)

- **Example**:
  ```python
  from core.regions import split_columns
  
  regions = split_columns(img, deg_start=0, deg_end=180, width=50)
  # regions[90] contains image slice for 90° region
  ```

---

### `core/io.py`
Handles file I/O operations for CZI images and CSV/JSON exports.

**Functions**:

**`load_czi(path)` → np.ndarray**
- Loads CZI microscope image files
- Automatically converts to grayscale if needed
- Returns normalized float32 image

**`get_pixel_size_um(path)` → float**
- Extracts pixel size from CZI metadata
- Default fallback: 0.34 µm if extraction fails
- Results cached to avoid re-parsing

**`save_image(path, img)`**
- Saves image using OpenCV

**`save_csv(path, rows)` → None**
- Saves list of dicts as CSV using pandas

- **Example**:
  ```python
  from core import io
  
  img = io.load_czi("sample.czi")
  pixel_size = io.get_pixel_size_um("sample.czi")
  
  results = [
      {"id": 1, "diameter_um": 12.34},
      {"id": 2, "diameter_um": 15.67}
  ]
  io.save_csv("results.csv", results)
  ```

---

### `core/statistics.py`
Computes statistical measures on detected blobs.

**Function: `compute_statistics(blobs, pixel_size_um=0.34)` → dict**
- **Parameters**:
  - `blobs` (list): List of blob dictionaries
  - `pixel_size_um` (float): Pixel size in micrometers

- **Returns**: Dictionary with statistics
  ```python
  {
    'mean': float,     # Mean diameter in µm
    'std': float,      # Standard deviation in µm
    'cv': float,       # Coefficient of variation (%)
    'count': int       # Number of blobs
  }
  ```

- **Example**:
  ```python
  from core.statistics import compute_statistics
  
  stats = compute_statistics(blobs, pixel_size_um=0.34)
  print(f"Mean diameter: {stats['mean']:.2f} µm")
  print(f"Std deviation: {stats['std']:.2f} µm")
  print(f"CV: {stats['cv']:.1f}%")
  ```

---

### `core/roi.py`
Region of Interest selection and management.

**Class: `ROI`**
A dataclass representing a rectangular region of interest.

- **Attributes**:
  - `x1, y1, x2, y2` (int): Corner coordinates
  - `width` (property): Width in pixels
  - `height` (property): Height in pixels

- **Methods**:
  - `crop_image(img)`: Returns cropped image array
  - `to_dict()`: Serialize to dictionary
  - `from_dict(d)`: Deserialize from dictionary

- **Example**:
  ```python
  from core.roi import ROI
  
  roi = ROI(x1=100, y1=150, x2=600, y2=700)
  cropped = roi.crop_image(img)
  print(f"ROI size: {roi.width}x{roi.height}px")
  
  # Save/load
  roi_dict = roi.to_dict()
  roi_loaded = ROI.from_dict(roi_dict)
  ```

**Class: `ROISelector`**
Interactive GUI for selecting regions of interest on images.

- **Constructor**: `ROISelector(img)`
  - `img` (np.ndarray): Image to select ROI from

- **Attributes**:
  - `roi` (ROI): Selected ROI (None if not yet selected)
  - `accepted` (bool): Whether selection was accepted
  - `finished` (bool): Whether selection is complete

- **Methods**:
  - `run()`: Display interactive selector (blocking)
    - Drag to draw rectangle
    - Press Enter to accept
    - Press Esc to cancel
  - Returns: Selected `ROI` object or None

- **Example**:
  ```python
  from core.roi import ROISelector
  
  selector = ROISelector(img)
  roi = selector.run()
  
  if roi:
      cropped_img = roi.crop_image(img)
      print(f"Selected ROI: {roi}")
  ```

---

### `core/interaction.py`
Interactive manual review interface for blob selection.

**Class: `ManualReviewInterface`**
Interactive matplotlib-based interface for accepting/rejecting detected blobs.

- **Constructor**: `ManualReviewInterface(img, blobs)`
  - `img` (np.ndarray): Image array
  - `blobs` (list): List of blob dictionaries

- **Attributes**:
  - `selected` (list[bool]): Selection state for each blob
  - `finished` (bool): Whether review is complete
  - `patches` (list): Matplotlib patch objects

- **Methods**:
  - `run()` → List[dict]: Display interface and return selected blobs
    - **Keyboard shortcuts**:
      - `A`: Select all blobs
      - `D`: Deselect all blobs
      - `Enter`: Accept and close
      - `Esc`: Cancel and keep all
    - **Mouse**: Click blob patches to toggle selection

- **Visual Feedback**:
  - Green edges: Selected (wanted)
  - Red edges: Rejected (unwanted)

- **Example**:
  ```python
  from core.interaction import ManualReviewInterface
  
  interface = ManualReviewInterface(processed_img, detected_blobs)
  selected_blobs = interface.run()
  print(f"User selected {len(selected_blobs)}/{len(detected_blobs)} blobs")
  ```

**Function: `manual_select(img, blobs)` → List[dict]**
Convenience wrapper around `ManualReviewInterface`.

- **Parameters**:
  - `img` (np.ndarray): Image to display
  - `blobs` (list): Blobs to review

- **Returns**: List of selected blob dictionaries

---

### `core/interactive_tuner.py`
Interactive parameter tuning with real-time preview.

**Dataclass: `DetectionParams`**
Container for all detection parameters.

```python
@dataclass
class DetectionParams:
    clahe_clip: float = 2.0          # CLAHE clipping limit
    tophat_kernel: int = 15          # Morphological kernel size
    median_kernel: int = 3           # Median blur kernel
    threshold: int = 80              # Binary threshold
    morph_iter: int = 2              # Morphological iterations
    min_diam: float = 5              # Minimum diameter (px)
    max_diam: float = 200            # Maximum diameter (px)
```

**Class: `InteractiveTuner`**
Real-time interactive parameter optimization with matplotlib sliders.

- **Constructor**: `InteractiveTuner(img, material="glass", max_blobs=8)`
  - `img` (np.ndarray): Image to tune on
  - `material` (str): "glass" or "aluminum"
  - `max_blobs` (int): Maximum blobs to display

- **Methods**:
  - `run()`: Display tuner interface
    - Returns: Tuned `DetectionParams` object
    - **Sliders**:
      - CLAHE [0.5-10]
      - Tophat [3-80]
      - Threshold [1-255]
      - Min diameter [1-150]
      - Max diameter [10-400]
      - Morphological iterations [1-10]

- **Example**:
  ```python
  from core.interactive_tuner import InteractiveTuner
  
  tuner = InteractiveTuner(processed_img, material="glass", max_blobs=8)
  tuned_params = tuner.run()
  
  # Use tuned parameters for detection
  blobs = detect_blobs(processed_img, {
      "threshold": tuned_params.threshold,
      "morph_iter": tuned_params.morph_iter,
      "min_diam": tuned_params.min_diam,
      "max_diam": tuned_params.max_diam
  })
  ```

**Functions for saving/loading parameters**:

**`save_params(params, path)` → None**
- Saves `DetectionParams` to JSON file

**`load_params(path)` → DetectionParams**
- Loads parameters from JSON file

---

### `core/threshold_optimizer.py`
Automatically finds optimal threshold to detect a target number of blobs.

**Function: `optimize_threshold(...)`**
Binary search algorithm to find optimal detection threshold.

- **Parameters**:
  - `img` (np.ndarray): Input image
  - `target_count` (int): Desired number of blobs
  - `material` (str): "glass" or "aluminum" [default: "glass"]
  - `max_blobs` (int): Maximum blobs to consider [default: 8]
  - `min_diam, max_diam` (float): Size constraints [default: 5-200]
  - `morph_iter, clahe_clip, tophat_kernel, median_kernel` (float/int): Processing parameters
  - `callback` (callable): Optional progress callback: `fn(threshold, count, status)`

- **Returns**: Dictionary
  ```python
  {
    'threshold': int,        # Optimal threshold found
    'blob_count': int,       # Number of blobs detected
    'blobs': list,          # Detected blob dictionaries
    'history': list         # Search history
  }
  ```

- **Algorithm**: Binary search with 12 max iterations (~log2(256))

- **Output**:
  - Prints iteration details to console
  - Calls callback function with progress updates

- **Example**:
  ```python
  from core.threshold_optimizer import optimize_threshold
  from core.preprocessing import preprocess
  from config import MATERIAL_PRESETS
  
  preset = MATERIAL_PRESETS["glass"]
  processed = preprocess(raw_img, preset)
  
  result = optimize_threshold(
      processed,
      target_count=5,
      material="glass",
      max_blobs=8,
      min_diam=5,
      max_diam=200
  )
  
  print(f"Found threshold: {result['threshold']}")
  print(f"Detected {result['blob_count']} blobs")
  optimal_blobs = result['blobs']
  ```

---

## Class API Documentation

### Complete Type Signatures

```python
# detection.py
def detect_blobs(
    img: np.ndarray,
    params: Dict[str, Any]
) -> List[Dict[str, Any]]: ...

# preprocessing.py
def preprocess(
    img: np.ndarray,
    preset: Dict[str, Any]
) -> np.ndarray: ...

# filtering.py
def filter_blobs(
    blobs: List[Dict],
    max_blobs: int
) -> List[Dict]: ...

# statistics.py
def compute_statistics(
    blobs: List[Dict],
    pixel_size_um: float = 0.34
) -> Dict[str, float]: ...

# io.py
def load_czi(path: str) -> np.ndarray: ...
def get_pixel_size_um(path: str) -> float: ...
def save_csv(path: str, rows: List[Dict]) -> None: ...

# roi.py
class ROI:
    x1: int
    y1: int
    x2: int
    y2: int
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    def crop_image(self, img: np.ndarray) -> np.ndarray: ...
    def to_dict(self) -> Dict: ...
    @staticmethod
    def from_dict(d: Dict) -> ROI: ...

class ROISelector:
    def __init__(self, img: np.ndarray): ...
    def run(self) -> Optional[ROI]: ...

# interaction.py
class ManualReviewInterface:
    def __init__(self, img: np.ndarray, blobs: List[Dict]): ...
    def run(self) -> List[Dict]: ...

def manual_select(img: np.ndarray, blobs: List[Dict]) -> List[Dict]: ...

# interactive_tuner.py
class InteractiveTuner:
    def __init__(self, img: np.ndarray, material: str = "glass", max_blobs: int = 8): ...
    def run(self) -> DetectionParams: ...

def save_params(params: DetectionParams, path: str) -> None: ...
def load_params(path: str) -> DetectionParams: ...

# threshold_optimizer.py
def optimize_threshold(
    img: np.ndarray,
    target_count: int,
    material: str = "glass",
    max_blobs: int = 8,
    min_diam: float = 5,
    max_diam: float = 200,
    morph_iter: int = 2,
    clahe_clip: float = 2.0,
    tophat_kernel: int = 15,
    median_kernel: int = 3,
    callback: Optional[Callable] = None
) -> Dict[str, Any]: ...
```

---

## Usage Examples

### Example 1: Basic Detection Pipeline

```python
from core import io, preprocessing, detection, filtering, statistics
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS

# Load image
img = io.load_czi("sample.czi")
pixel_size = io.get_pixel_size_um("sample.czi")

# Preprocess
preset = MATERIAL_PRESETS["glass"]
processed = preprocessing.preprocess(img, preset)

# Detect
blobs = detection.detect_blobs(processed, {
    **DETECTION_DEFAULTS,
    "min_diam": 5,
    "max_diam": 200
})

# Filter
filtered_blobs = filtering.filter_blobs(blobs, max_blobs=8)

# Analyze
stats = statistics.compute_statistics(filtered_blobs, pixel_size)

print(f"Detected {len(filtered_blobs)} blobs")
print(f"Mean diameter: {stats['mean']:.2f} µm")
print(f"Std deviation: {stats['std']:.2f} µm")
```

### Example 2: Interactive Tuning

```python
from core import io, preprocessing
from core.interactive_tuner import InteractiveTuner, save_params
from config import MATERIAL_PRESETS

# Load and preprocess
img = io.load_czi("sample.czi")
preset = MATERIAL_PRESETS["glass"]
processed = preprocessing.preprocess(img, preset)

# Launch interactive tuner
tuner = InteractiveTuner(processed, material="glass")
tuned_params = tuner.run()

# Save tuned parameters for future use
save_params(tuned_params, "my_tuned_params.json")

print(f"Tuned parameters saved!")
print(f"Optimal threshold: {tuned_params.threshold}")
```

### Example 3: Manual Review

```python
from core import io, preprocessing, detection
from core.interaction import manual_select
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS

# Load and process
img = io.load_czi("sample.czi")
preset = MATERIAL_PRESETS["glass"]
processed = preprocessing.preprocess(img, preset)

# Detect automatically
blobs = detection.detect_blobs(processed, DETECTION_DEFAULTS)

# Manual review
reviewed_blobs = manual_select(processed, blobs)

print(f"User selected {len(reviewed_blobs)}/{len(blobs)} blobs")
```

### Example 4: Automated Threshold Optimization

```python
from core import io, preprocessing
from core.threshold_optimizer import optimize_threshold
from config import MATERIAL_PRESETS

# Load and preprocess
img = io.load_czi("sample.czi")
preset = MATERIAL_PRESETS["glass"]
processed = preprocessing.preprocess(img, preset)

# Auto-optimize to detect exactly 5 blobs
result = optimize_threshold(
    processed,
    target_count=5,
    material="glass",
    min_diam=5,
    max_diam=200
)

optimal_blobs = result['blobs']
print(f"Found {len(optimal_blobs)} blobs with threshold {result['threshold']}")
```

### Example 5: ROI Selection

```python
from core import io
from core.roi import ROISelector

# Load image
img = io.load_czi("sample.czi")

# Select ROI interactively
selector = ROISelector(img)
roi = selector.run()

if roi:
    cropped = roi.crop_image(img)
    print(f"Cropped to {roi.width}x{roi.height}px")
    print(f"ROI: ({roi.x1},{roi.y1}) to ({roi.x2},{roi.y2})")
    
    # Save ROI for future use
    roi_dict = roi.to_dict()
    # ... save to JSON
```

---

## Workflows

### Workflow 1: One-Time Analysis

```
Load Image → Preprocess → Detect → Filter → Analyze → Export Results
```

**Code**:
```python
from core import io, preprocessing, detection, filtering, statistics

img = io.load_czi("sample.czi")
processed = preprocessing.preprocess(img, MATERIAL_PRESETS["glass"])
blobs = detection.detect_blobs(processed, DETECTION_DEFAULTS)
filtered = filtering.filter_blobs(blobs, 8)
stats = statistics.compute_statistics(filtered)
io.save_csv("results.csv", stats)
```

---

### Workflow 2: Parameter Optimization

```
Load Image → Preprocess → Interactive Tuning → Save Parameters → Use for Batch Processing
```

**Code**:
```python
from core import io, preprocessing
from core.interactive_tuner import InteractiveTuner, save_params

img = io.load_czi("sample.czi")
processed = preprocessing.preprocess(img, MATERIAL_PRESETS["glass"])

tuner = InteractiveTuner(processed)
params = tuner.run()
save_params(params, "optimized_params.json")

# Later, load and use these params...
```

---

### Workflow 3: Guided Detection with Validation

```
Load → Preprocess → Auto-Optimize Threshold → Manual Review → Statistics → Save
```

**Code**:
```python
from core import io, preprocessing
from core.threshold_optimizer import optimize_threshold
from core.interaction import manual_select
from core.statistics import compute_statistics

img = io.load_czi("sample.czi")
processed = preprocessing.preprocess(img, MATERIAL_PRESETS["glass"])

# Auto-optimize
result = optimize_threshold(processed, target_count=5)
auto_blobs = result['blobs']

# Manual validation
validated = manual_select(processed, auto_blobs)

# Analysis
stats = compute_statistics(validated)
print(f"Final result: {stats}")
```

---

### Workflow 4: Batch Processing with ROI

```
For Each Image:
  Load → Select ROI → Crop → Preprocess → Detect → Analyze → Save Results
```

**Code**:
```python
from core import io, preprocessing, detection, statistics
from core.roi import load_roi

# Load pre-defined ROI
roi = load_roi("roi_template.json")

image_files = ["img1.czi", "img2.czi", "img3.czi"]
all_results = []

for img_file in image_files:
    img = io.load_czi(img_file)
    cropped = roi.crop_image(img)
    
    processed = preprocessing.preprocess(cropped, MATERIAL_PRESETS["glass"])
    blobs = detection.detect_blobs(processed, DETECTION_DEFAULTS)
    
    stats = statistics.compute_statistics(blobs)
    stats['image'] = img_file
    all_results.append(stats)

io.save_csv("batch_results.csv", all_results)
```

---

## Configuration

### `config.py` - Global Configuration

```python
MATERIAL_PRESETS = {
    "glass": {
        "clahe_clip": 2.0,          # CLAHE clipping limit
        "tophat_kernel": 15,        # Black-hat kernel size
        "median_kernel": 3,         # Median blur kernel
        "invert": False,            # Don't invert image
        "scratch_removal": False    # No scratch removal needed
    },
    "aluminum": {
        "clahe_clip": 2.0,
        "tophat_kernel": 25,        # Larger kernel for aluminum
        "median_kernel": 3,
        "invert": True,            # Invert image for aluminum
        "scratch_removal": True     # Enable scratch removal
    }
}

DETECTION_DEFAULTS = {
    "threshold": 120,              # Binary threshold
    "morph_iter": 2,              # Morphological iterations
    "min_diam": 5,                # Minimum blob diameter (px)
    "max_diam": 200,              # Maximum blob diameter (px)
    "max_blobs": 8                # Maximum blobs to report
}
```

### Custom Presets

Create custom material presets by modifying `config.py`:

```python
MATERIAL_PRESETS["myCustom"] = {
    "clahe_clip": 3.0,
    "tophat_kernel": 20,
    "median_kernel": 5,
    "invert": False,
    "scratch_removal": True
}

# Then use it:
preset = MATERIAL_PRESETS["myCustom"]
processed = preprocessing.preprocess(img, preset)
```

---

## GUI Guide

### Main Application (`gui/main_window.py`)

Run GUI with:
```bash
python main.py
```

### Available Controls

| Button | Function |
|--------|----------|
| **Load CZI** | Open microscope image file |
| **Analyze** | Run detection and analysis |
| **Tune parameters** | Interactive parameter optimization |
| **Auto-Optimize Threshold** | Binary search to find target blob count |
| **Select ROI** | Define region of interest |
| **Save ROI** | Save ROI to JSON file |
| **Load ROI** | Load previously saved ROI |
| **Clear ROI** | Remove current ROI |
| **Save preset** | Save detection parameters |
| **Load preset** | Load previously saved parameters |
| **Save Results** | Export analysis results |

### Dropdowns

- **Material**: Choose between "glass" and "aluminum" presets
- **Enable manual review**: Checkbox to show manual validation interface

---

## Troubleshooting

### Issue: "ImportError: Failed to import any of the following Qt binding modules"

**Solution**: Install PyQt5
```bash
pip install PyQt5
```

### Issue: "CZI file not found" or path errors

**Solution**: Use absolute paths or verify file exists
```python
import os
assert os.path.exists("path/to/file.czi"), "File not found"
img = io.load_czi("path/to/file.czi")
```

### Issue: Detected blob count is 0

**Troubleshooting**:
1. Check image is loaded correctly: `print(img.shape, img.dtype)`
2. Verify preprocessing output: `print(processed.min(), processed.max())`
3. Try with lower threshold: `threshold: 50`
4. Use interactive tuner to find optimal parameters
5. Check material preset (glass vs aluminum)

### Issue: Too many/few blobs detected

**Solution**: Use threshold optimizer
```python
result = optimize_threshold(processed, target_count=5)
optimal_threshold = result['threshold']
```

Or manually tune using:
```python
tuner = InteractiveTuner(processed)
params = tuner.run()
```

### Issue: Manual review interface doesn't respond

**Solution**: Ensure you're using the Qt5Agg backend
```python
import matplotlib
matplotlib.use('Qt5Agg')
```

This is configured automatically in `interaction.py`.

### Issue: Memory error with large images

**Solution**: Use ROI selection to work with subsets
```python
roi = ROISelector(img).run()
cropped = roi.crop_image(img)  # Process smaller region
```

---

## Advanced Topics

### Custom Preprocessing

```python
def custom_preprocess(img):
    """Your custom preprocessing pipeline."""
    import cv2
    # Your custom steps
    return processed_img

result = custom_preprocess(raw_img)
blobs = detection.detect_blobs(result, DETECTION_DEFAULTS)
```

### Batch Processing Template

```python
import glob
from core import io, preprocessing, detection, filtering, statistics
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS

def process_batch(image_dir, output_file):
    """Process all CZI files in directory."""
    
    image_files = glob.glob(f"{image_dir}/*.czi")
    results = []
    
    for img_file in image_files:
        try:
            # Load and process
            img = io.load_czi(img_file)
            preset = MATERIAL_PRESETS["glass"]
            processed = preprocessing.preprocess(img, preset)
            blobs = detection.detect_blobs(processed, DETECTION_DEFAULTS)
            filtered = filtering.filter_blobs(blobs, 8)
            
            # Compute statistics
            pixel_size = io.get_pixel_size_um(img_file)
            stats = statistics.compute_statistics(filtered, pixel_size)
            stats['filename'] = img_file
            
            results.append(stats)
            print(f"✓ {img_file}")
        except Exception as e:
            print(f"✗ {img_file}: {e}")
    
    # Save results
    io.save_csv(output_file, results)
    print(f"\nProcessed {len(results)} files. Results saved to {output_file}")

# Usage
process_batch("./images", "batch_results.csv")
```

### Extending with Custom Classes

```python
from core.roi import ROI

class CustomROI(ROI):
    """Extended ROI with metadata."""
    
    def __init__(self, x1, y1, x2, y2, name=None):
        super().__init__(x1, y1, x2, y2)
        self.name = name or f"ROI_{x1}_{y1}"
    
    def __repr__(self):
        return f"{self.name}: {self.width}x{self.height}px"
```

---

## Performance Notes

- **Preprocessing**: ~50-200ms for typical CZI image
- **Detection**: ~100-500ms depending on image size and parameters
- **Interactive Tuner**: Real-time (<100ms) updates with slider interaction
- **Threshold Optimization**: ~1-5 seconds (12 iterations max)
- **Manual Review**: Interactive, no time constraint

Optimize performance by:
1. Using ROI to reduce image size
2. Increasing `max_blobs` parameter (limits search space)
3. Tightening `min_diam`/`max_diam` constraints

---

## Contributing & Support

For bugs, questions, or suggestions:
- Check existing issues in GitHub
- Create detailed bug reports with:
  - Python version
  - OS/platform
  - Error traceback
  - Sample image (if possible)

---

## License

[Specify your license here]

---

## Changelog

### Version 1.0 (Current)
- ✓ Core detection and preprocessing
- ✓ Interactive parameter tuning
- ✓ Manual review interface
- ✓ Threshold optimization
- ✓ ROI selection
- ✓ Statistics computation
- ✓ GUI application
- ✓ CZI file support

---

## References

### Key Libraries
- **OpenCV (cv2)**: Image processing
- **NumPy**: Numerical computing
- **SciPy**: Statistical functions
- **Pandas**: Data export
- **Matplotlib**: Visualization
- **PySide6**: GUI framework
- **czifile**: CZI image loading

### Papers/Resources
- Morphological Image Processing
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Blob Detection using Contours

---

**Last Updated**: February 2026

**For questions or support, contact the development team.**
