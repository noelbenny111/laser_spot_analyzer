# core/roi.py
"""
Region of Interest (ROI) selection and management.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from dataclasses import dataclass

@dataclass
class ROI:
    """Region of Interest coordinates."""
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self):
        return self.x2 - self.x1
    
    @property
    def height(self):
        return self.y2 - self.y1
    
    def to_dict(self):
        return {'x1': self.x1, 'y1': self.y1, 'x2': self.x2, 'y2': self.y2}
    
    @staticmethod
    def from_dict(d):
        return ROI(d['x1'], d['y1'], d['x2'], d['y2'])
    
    def crop_image(self, img):
        """Crop image to this ROI."""
        return img[self.y1:self.y2, self.x1:self.x2].copy()
    
    def __str__(self):
        return f"ROI({self.x1}, {self.y1}, {self.x2}, {self.y2}) - {self.width}x{self.height}px"


class ROISelector:
    """Interactive ROI selector with live preview."""
    
    def __init__(self, img):
        self.img = img
        self.roi = None
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        plt.subplots_adjust(bottom=0.15)
        
        self.ax.imshow(img, cmap='gray')
        self.ax.set_title("Select Region of Interest (ROI)\nDrag to draw rectangle, press Enter to accept, Esc to cancel",
                         fontsize=12, pad=10)
        
        self.rect_selector = RectangleSelector(
            self.ax,
            self.on_select,
            useblit=True,
            button=[1],  # Left mouse button
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=True,
            props=dict(facecolor='red', edgecolor='green', alpha=0.3, linewidth=2)
        )
        
        self.finished = False
        self.accepted = False
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
    
    def on_select(self, eclick, erelease):
        """Called when rectangle is selected."""
        x1 = int(min(eclick.xdata, erelease.xdata))
        y1 = int(min(eclick.ydata, erelease.ydata))
        x2 = int(max(eclick.xdata, erelease.xdata))
        y2 = int(max(eclick.ydata, erelease.ydata))
        
        self.roi = ROI(x1, y1, x2, y2)
        
        # Update title with ROI info
        self.ax.set_title(
            f"ROI Selected: {self.roi.width}x{self.roi.height}px at ({x1}, {y1})\n"
            f"Press Enter to accept, Esc to cancel, or draw new ROI",
            fontsize=12, pad=10
        )
        self.fig.canvas.draw_idle()
        
        print(f"[ROI] Selected: {self.roi}")
    
    def _on_key_press(self, event):
        """Handle keyboard events."""
        if event.key == 'enter':
            if self.roi is not None:
                self.accepted = True
                print(f"[ROI] Accepted: {self.roi}")
                plt.close(self.fig)
            else:
                print("[ROI] No ROI selected! Draw a rectangle first.")
        
        elif event.key == 'escape':
            print("[ROI] Selection cancelled")
            self.accepted = False
            plt.close(self.fig)
    
    def run(self):
        """Show the selector and return selected ROI."""
        print("[ROI] Opening ROI selector...")
        print("[ROI] Instructions:")
        print("  - Drag mouse to draw a rectangle on the image")
        print("  - Press 'Enter' to accept the ROI")
        print("  - Press 'Esc' to cancel")
        
        plt.show(block=False)
        
        # Process events until user finishes
        while not self.finished and plt.fignum_exists(self.fig.number):
            plt.pause(0.1)
        
        plt.pause(0.2)
        
        if self.accepted and self.roi:
            print(f"[ROI] Returning ROI: {self.roi}")
            return self.roi
        else:
            print("[ROI] No ROI selected")
            return None


def select_roi(img):
    """Interactive ROI selection."""
    selector = ROISelector(img)
    return selector.run()


def save_roi(roi, path):
    """Save ROI to JSON file."""
    with open(path, 'w') as f:
        json.dump(roi.to_dict(), f, indent=2)
    print(f"[ROI] Saved to {path}")


def load_roi(path):
    """Load ROI from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    roi = ROI.from_dict(data)
    print(f"[ROI] Loaded: {roi}")
    return roi
