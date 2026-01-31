from PySide6.QtWidgets import (
    QWidget, QPushButton, QFileDialog, QVBoxLayout,
    QComboBox, QCheckBox, QLabel
)
from core import io, preprocessing, detection, filtering, interaction, statistics, regions
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS
import os
import cv2
from core.interactive_tuner import (
    InteractiveTuner,
    DetectionParams,
    save_params,
    load_params,
)
class LaserSpotAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laser Spot Analyzer")

        self.material = QComboBox()
        self.material.addItems(["glass", "aluminum"])

        self.review = QCheckBox("Enable manual review")
        self.load_btn = QPushButton("Load CZI")
        self.run_btn = QPushButton("Analyze")
        self.active_params = DetectionParams()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Material"))
        layout.addWidget(self.material)
        layout.addWidget(self.review)
        layout.addWidget(self.load_btn)
        layout.addWidget(self.run_btn)

        self.load_btn.clicked.connect(self.load)
        self.run_btn.clicked.connect(self.run)
        self.tune_btn = QPushButton("Tune parameters")
        self.save_btn = QPushButton("Save preset")
        self.load_preset_btn = QPushButton("Load preset")

        layout.addWidget(self.tune_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_preset_btn)

        self.tune_btn.clicked.connect(self.tune_parameters)
        self.save_btn.clicked.connect(self.save_preset)
        self.load_preset_btn.clicked.connect(self.load_preset)

        
    def load(self):
        self.path, _ = QFileDialog.getOpenFileName(self, "Select CZI", "", "*.czi")

    def tune_parameters(self):
        if not hasattr(self, "path") or self.path is None:
            print("No image loaded for tuning.")
            return

        img = io.load_czi(self.path)
        tuner = InteractiveTuner(
            img,
            material=self.material.currentText(),
            max_blobs=DETECTION_DEFAULTS["max_blobs"]
        )
        blobs, params = tuner.run()

        if params is not None:
            self.active_params = params
            print("Updated active parameters:")
            print(self.active_params)

    def save_preset(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save parameter preset",
            "",
            "JSON Files (*.json)"
        )
        if path:
            save_params(self.active_params, path)
            print(f"Saved preset to {path}")

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load parameter preset",
            "",
            "JSON Files (*.json)"
        )
        if path:
            self.active_params = load_params(path)
            print("Loaded preset:")
            print(self.active_params)

    def run(self):
        if not hasattr(self, "path") or self.path is None:
            print("No image loaded. Please load a CZI file first.")
            return

        img = io.load_czi(self.path)
        px = io.get_pixel_size_um(self.path)

        # ---------------- PREPROCESSING ----------------
        preset = MATERIAL_PRESETS[self.material.currentText()].copy()

        # override with tuned params
        preset["clahe_clip"] = self.active_params.clahe_clip
        preset["tophat_kernel"] = self.active_params.tophat_kernel
        preset["median_kernel"] = self.active_params.median_kernel

        proc = preprocessing.preprocess(img, preset)

        # ---------------- DETECTION ----------------
        detect_params = {
            **DETECTION_DEFAULTS,
            "threshold": self.active_params.threshold,
            "morph_iter": self.active_params.morph_iter,
            "min_diam": self.active_params.min_diam,
            "max_diam": self.active_params.max_diam,
        }

        blobs = detection.detect_blobs(proc, detect_params)
        blobs = filtering.filter_blobs(blobs, detect_params["max_blobs"])

        # ---------------- OPTIONAL REVIEW ----------------
        if self.review.isChecked():
            blobs = interaction.manual_select(proc, blobs)

        # ---------------- STATISTICS ----------------
        diam_um = [b["diam_px"] * px for b in blobs]
        mean, std, coeff_var, ci = statistics.compute_stats(diam_um)

        print(f"Detected {len(blobs)} blobs")
        print(f"Mean diameter: {mean:.2f} µm | CV: {coeff_var:.2f} %")

        # ---------------- SAVE OUTPUT ----------------
        out = os.path.splitext(self.path)[0] + "_annotated.png"
        ann = cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR)

        for b in blobs:
            if b["ellipse"]:
                cv2.ellipse(ann, b["ellipse"], (0, 255, 0), 2)

        io.save_image(out, ann)
        print(f"Saved annotated image: {out}")
