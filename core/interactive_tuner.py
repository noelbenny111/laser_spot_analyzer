# core/interactive_tuner.py

from dataclasses import dataclass
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend for compatibility with PySide6
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Ellipse, Circle
import numpy as np

from core.preprocessing import preprocess
from core.detection import detect_blobs
from core.filtering import filter_blobs
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS

@dataclass
class DetectionParams:
    clahe_clip: float = 2.0
    tophat_kernel: int = 15
    median_kernel: int = 3
    threshold: int = 80
    morph_iter: int = 2
    min_diam: float = 5
    max_diam: float = 200

class InteractiveTuner:
    def __init__(self, img, material="glass", max_blobs=8):
        self.img = img
        self.material = material
        self.max_blobs = max_blobs
        self.params = DetectionParams()
        self.final_blobs = []
        self.finished = False
        
        # Create figure with image
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        plt.subplots_adjust(bottom=0.50)
        
        # Create sliders
        ax_clahe = plt.axes([0.2, 0.42, 0.6, 0.03])
        ax_tophat = plt.axes([0.2, 0.37, 0.6, 0.03])
        ax_thresh = plt.axes([0.2, 0.32, 0.6, 0.03])
        ax_min = plt.axes([0.2, 0.27, 0.6, 0.03])
        ax_max = plt.axes([0.2, 0.22, 0.6, 0.03])
        ax_morph = plt.axes([0.2, 0.17, 0.6, 0.03])
        ax_button = plt.axes([0.4, 0.08, 0.2, 0.04])
        
        self.s_clahe = Slider(ax_clahe, "CLAHE", 0.5, 10, valinit=self.params.clahe_clip)
        self.s_tophat = Slider(ax_tophat, "Tophat", 3, 80, valinit=self.params.tophat_kernel, valstep=1)
        self.s_thresh = Slider(ax_thresh, "Threshold", 1, 255, valinit=self.params.threshold)
        self.s_min = Slider(ax_min, "Min diam", 1, 150, valinit=self.params.min_diam)
        self.s_max = Slider(ax_max, "Max diam", 10, 400, valinit=self.params.max_diam)
        self.s_morph = Slider(ax_morph, "Morph", 1, 10, valinit=self.params.morph_iter, valstep=1)
        
        self.button = Button(ax_button, "Accept")
        
        # Connect slider events - use lambda to ensure update is called
        self.s_clahe.on_changed(lambda x: self._update_preview())
        self.s_tophat.on_changed(lambda x: self._update_preview())
        self.s_thresh.on_changed(lambda x: self._update_preview())
        self.s_min.on_changed(lambda x: self._update_preview())
        self.s_max.on_changed(lambda x: self._update_preview())
        self.s_morph.on_changed(lambda x: self._update_preview())
        
        self.button.on_clicked(self.finish)
        
        # Initial render
        self._update_preview()

    
    def _update_preview(self):
        """Update the preview image with current parameters."""
        try:
            # Read current slider values
            params = DetectionParams(
                clahe_clip=self.s_clahe.val,
                tophat_kernel=int(self.s_tophat.val),
                threshold=int(self.s_thresh.val),
                min_diam=self.s_min.val,
                max_diam=self.s_max.val,
                morph_iter=int(self.s_morph.val),
                median_kernel=self.params.median_kernel
            )
            
            # Preprocess image
            preset = MATERIAL_PRESETS[self.material].copy()
            preset["clahe_clip"] = params.clahe_clip
            preset["tophat_kernel"] = params.tophat_kernel
            preset["median_kernel"] = params.median_kernel
            
            proc = preprocess(self.img, preset)
            
            # Detect blobs
            blobs = detect_blobs(proc, {
                **DETECTION_DEFAULTS,
                "threshold": params.threshold,
                "morph_iter": params.morph_iter,
                "min_diam": params.min_diam,
                "max_diam": params.max_diam
            })
            
            # Filter blobs
            blobs = filter_blobs(blobs, self.max_blobs)
            
            # Update display
            self.ax.clear()
            self.ax.imshow(proc, cmap="gray")
            
            for b in blobs:
                if b["ellipse"]:
                    e = Ellipse(b["ellipse"][0], *b["ellipse"][1],
                                angle=b["ellipse"][2],
                                edgecolor="red", facecolor="none", linewidth=2)
                    self.ax.add_patch(e)
                else:
                    c = Circle(b["center"], b["diam_px"]/2,
                               edgecolor="red", facecolor="none", linewidth=2)
                    self.ax.add_patch(c)
            
            self.ax.set_title(f"{len(blobs)} blobs | T:{int(params.threshold)} Morph:{int(params.morph_iter)}", fontsize=10)
            self.ax.axis("off")
            
            # Force redraw
            self.fig.canvas.draw_idle()
            
            # Store results
            self.final_blobs = blobs
            self.params = params
            
            # Debug output
            if len(blobs) > 0:
                print(f"  [PREVIEW] {len(blobs)} blobs detected, threshold={int(params.threshold)}")
            
        except Exception as e:
            print(f"Error updating preview: {e}")
            import traceback
            traceback.print_exc()
    
    def finish(self, event):
        """Close the tuner when Accept button is clicked."""
        # Ensure we have valid data before closing
        print(f"[TUNER] Accept clicked!")
        print(f"  - Blobs stored: {len(self.final_blobs)}")
        print(f"  - Params stored: threshold={int(self.params.threshold)}, morph={int(self.params.morph_iter)}")
        
        # Verify data integrity
        if len(self.final_blobs) == 0:
            print(f"  [WARNING] No blobs detected! Using current parameters only.")
        
        self.finished = True
        plt.close(self.fig)
    
    def run(self):
        """Show the tuner and return final parameters."""
        print("[TUNER] Starting interactive tuning...")
        print("[TUNER] Adjust sliders and click Accept when done")
        
        # Show window non-blocking (compatible with Qt event loop)
        plt.show(block=False)
        
        # Process events until user closes window
        import time
        while not self.finished and plt.fignum_exists(self.fig.number):
            plt.pause(0.1)  # Small pause to prevent CPU spinning
        
        # Final pause to ensure all events processed
        plt.pause(0.2)
        
        # Verify data before returning
        print(f"\n[TUNER] Window closed.")
        print(f"[TUNER] Returning data:")
        print(f"  - Blobs: {len(self.final_blobs)}")
        print(f"  - Params: {self.params}")
        
        # Safety check
        if self.params is None:
            print(f"[WARNING] Params is None! Using default.")
            self.params = DetectionParams()
        
        if self.final_blobs is None:
            print(f"[WARNING] Blobs is None! Using empty list.")
            self.final_blobs = []
        
        return self.final_blobs, self.params
    
import json
from dataclasses import asdict

def save_params(params, path):
    """
    Save DetectionParams to JSON.
    """
    with open(path, "w") as f:
        json.dump(asdict(params), f, indent=2)


def load_params(path):
    """
    Load DetectionParams from JSON.
    """
    with open(path, "r") as f:
        data = json.load(f)
    return DetectionParams(**data)
