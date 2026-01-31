# core/interactive_tuner.py

from dataclasses import dataclass
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Ellipse, Circle

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
# core/interactive_tuner.py

class InteractiveTuner:
    def __init__(self, img, material="glass", max_blobs=8):
        self.img = img
        self.material = material
        self.max_blobs = max_blobs
        self.params = DetectionParams()

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        plt.subplots_adjust(bottom=0.4)

        # --- sliders ---
        self.s_clahe = Slider(plt.axes([0.15, 0.30, 0.65, 0.03]),
                              "CLAHE", 0.5, 10, valinit=self.params.clahe_clip)
        self.s_tophat = Slider(plt.axes([0.15, 0.25, 0.65, 0.03]),
                               "Tophat", 3, 80, valinit=self.params.tophat_kernel, valstep=1)
        self.s_thresh = Slider(plt.axes([0.15, 0.20, 0.65, 0.03]),
                               "Threshold", 1, 255, valinit=self.params.threshold)
        self.s_min = Slider(plt.axes([0.15, 0.15, 0.65, 0.03]),
                            "Min diam", 1, 150, valinit=self.params.min_diam)
        self.s_max = Slider(plt.axes([0.15, 0.10, 0.65, 0.03]),
                            "Max diam", 10, 400, valinit=self.params.max_diam)
        self.s_morph = Slider(plt.axes([0.15, 0.05, 0.65, 0.03]),
                              "Morph", 1, 10, valinit=self.params.morph_iter, valstep=1)

        self.button = Button(plt.axes([0.82, 0.01, 0.15, 0.04]), "Accept")

        for s in [self.s_clahe, self.s_tophat, self.s_thresh,
                  self.s_min, self.s_max, self.s_morph]:
            s.on_changed(self.update)

        self.button.on_clicked(self.finish)

        self.finished = False
        self.final_blobs = []
        self.update(None)

    def update(self, _):
        # update params
        self.params.clahe_clip = self.s_clahe.val
        self.params.tophat_kernel = int(self.s_tophat.val)
        self.params.threshold = int(self.s_thresh.val)
        self.params.min_diam = self.s_min.val
        self.params.max_diam = self.s_max.val
        self.params.morph_iter = int(self.s_morph.val)

        preset = MATERIAL_PRESETS[self.material].copy()
        preset["clahe_clip"] = self.params.clahe_clip
        preset["tophat_kernel"] = self.params.tophat_kernel
        preset["median_kernel"] = self.params.median_kernel

        proc = preprocess(self.img, preset)

        blobs = detect_blobs(proc, {
            **DETECTION_DEFAULTS,
            "threshold": self.params.threshold,
            "morph_iter": self.params.morph_iter,
            "min_diam": self.params.min_diam,
            "max_diam": self.params.max_diam
        })

        blobs = filter_blobs(blobs, self.max_blobs)

        self.ax.clear()
        self.ax.imshow(proc, cmap="gray")

        for b in blobs:
            if b["ellipse"]:
                e = Ellipse(b["ellipse"][0], *b["ellipse"][1],
                            angle=b["ellipse"][2],
                            edgecolor="red", facecolor="none")
                self.ax.add_patch(e)
            else:
                c = Circle(b["center"], b["diam_px"]/2,
                           edgecolor="red", facecolor="none")
                self.ax.add_patch(c)

        self.ax.set_title(f"{len(blobs)} detected blobs")
        self.ax.axis("off")
        self.fig.canvas.draw_idle()

        self.final_blobs = blobs

    def finish(self, _):
        self.finished = True
        plt.close(self.fig)

    def run(self):
        plt.show()
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
