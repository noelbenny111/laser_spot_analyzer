from PySide6.QtWidgets import (
    QWidget, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QLabel, QSpinBox, QDialog
)
from core import io, preprocessing, detection, filtering, interaction, statistics, regions
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS
import os
import cv2
import sys
import json
import subprocess
from core.interactive_tuner import (
    InteractiveTuner,
    DetectionParams,
    save_params,
    load_params,
)
from core.threshold_optimizer import optimize_threshold
from core.roi import select_roi, save_roi, load_roi
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
        self.loaded_image = None  # Cache loaded image to avoid reloading
        self.loaded_path = None
        self.tuned_blobs = None  # Store blobs from tuner
        self.roi = None  # Region of Interest
        self.last_stats = None  # Store last analysis statistics
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Material"))
        layout.addWidget(self.material)
        layout.addWidget(self.review)
        layout.addWidget(self.load_btn)
        layout.addWidget(self.run_btn)

        self.load_btn.clicked.connect(self.load)
        self.run_btn.clicked.connect(self.run)
        self.tune_btn = QPushButton("Tune parameters")
        self.auto_optimize_btn = QPushButton("Auto-Optimize Threshold")
        self.save_btn = QPushButton("Save preset")
        self.load_preset_btn = QPushButton("Load preset")
        self.select_roi_btn = QPushButton("Select ROI (Region of Interest)")
        self.save_roi_btn = QPushButton("Save ROI")
        self.load_roi_btn = QPushButton("Load ROI")
        self.clear_roi_btn = QPushButton("Clear ROI")
        self.save_results_btn = QPushButton("Save Results")

        layout.addWidget(self.tune_btn)
        layout.addWidget(self.auto_optimize_btn)
        layout.addWidget(self.save_results_btn)
        
        # ROI section
        layout.addWidget(QLabel("--- Region of Interest ---"))
        roi_layout = QHBoxLayout()
        roi_layout.addWidget(self.select_roi_btn)
        roi_layout.addWidget(self.save_roi_btn)
        roi_layout.addWidget(self.load_roi_btn)
        roi_layout.addWidget(self.clear_roi_btn)
        layout.addLayout(roi_layout)
        self.roi_label = QLabel("ROI: Not selected")
        layout.addWidget(self.roi_label)
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_preset_btn)

        self.tune_btn.clicked.connect(self.tune_parameters)
        self.auto_optimize_btn.clicked.connect(self.auto_optimize)
        self.save_btn.clicked.connect(self.save_preset)
        self.load_preset_btn.clicked.connect(self.load_preset)
        self.save_results_btn.clicked.connect(self.save_results)
        self.select_roi_btn.clicked.connect(self.select_roi)
        self.save_roi_btn.clicked.connect(self.save_roi)
        self.load_roi_btn.clicked.connect(self.load_roi)
        self.clear_roi_btn.clicked.connect(self.clear_roi)

        
    def load(self):
        try:
            self.loaded_path, _ = QFileDialog.getOpenFileName(self, "Select CZI", "", "*.czi")
            if self.loaded_path:
                self.loaded_image = io.load_czi(self.loaded_path)
                self.tuned_blobs = None  # Reset tuned blobs when loading new image
                self.roi = None  # Reset ROI when loading new image
                self._update_roi_label()
                print(f"✓ Image loaded: {self.loaded_image.shape}")
        except Exception as e:
            import traceback
            print(f"ERROR loading CZI file: {e}")
            traceback.print_exc()

    def tune_parameters(self):
        try:
            if self.loaded_image is None:
                print("No image loaded for tuning.")
                return

            print("\n" + "="*60)
            print("PARAMETER TUNING")
            print("="*60)
            
            # Use ROI if available
            tuner_image = self.loaded_image
            if self.roi:
                print(f"✓ Using ROI: {self.roi}")
                tuner_image = self.roi.crop_image(self.loaded_image)
                print(f"  Cropped image: {tuner_image.shape}")
            
            tuner = InteractiveTuner(
                tuner_image,
                material=self.material.currentText(),
                max_blobs=DETECTION_DEFAULTS["max_blobs"]
            )
            print("[GUI] Created tuner, calling run()...")
            blobs, params = tuner.run()
            print(f"[GUI] Tuner returned: {len(blobs)} blobs, params={params}")

            if blobs is not None and params is not None:
                self.active_params = params
                self.tuned_blobs = blobs
                
                print(f"\n✓ Tuning complete!")
                print(f"  Parameters: {self.active_params}")
                print(f"  Blobs detected: {len(blobs)}")
                
                # If manual review is enabled, show review interface now
                if self.review.isChecked():
                    print("\n" + "="*60)
                    print("MANUAL REVIEW")
                    print("="*60)
                    from core.interaction import manual_select
                    try:
                        print("[GUI] Opening manual review interface...")
                        reviewed_blobs = manual_select(self.loaded_image, blobs)
                        self.tuned_blobs = reviewed_blobs
                        print(f"✓ Review complete: {len(reviewed_blobs)}/{len(blobs)} blobs selected")
                    except Exception as e:
                        print(f"Review error: {e}")
                        import traceback
                        traceback.print_exc()
                        self.tuned_blobs = blobs
                
            else:
                print(f"[WARNING] Tuner returned None values: blobs={blobs}, params={params}")
                
        except Exception as e:
            import traceback
            print(f"ERROR during parameter tuning: {e}")
            traceback.print_exc()

    def auto_optimize(self):
        """Auto-optimize threshold to detect a specific number of blobs."""
        try:
            if self.loaded_image is None:
                print("No image loaded for optimization.")
                return
            
            # Create dialog to get target blob count
            dialog = QDialog(self)
            dialog.setWindowTitle("Auto-Optimize Threshold")
            dialog.setGeometry(100, 100, 300, 120)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("Target number of blobs to detect:"))
            
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(20)
            spinbox.setValue(4)
            layout.addWidget(spinbox)
            
            ok_btn = QPushButton("Optimize")
            cancel_btn = QPushButton("Cancel")
            
            button_layout = QHBoxLayout()
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            target_count = None
            
            def on_ok():
                nonlocal target_count
                target_count = spinbox.value()
                dialog.accept()
            
            ok_btn.clicked.connect(on_ok)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
            
            if target_count is None:
                print("Optimization cancelled.")
                return
            
            print(f"\n{'='*60}")
            print(f"AUTO-OPTIMIZING for {target_count} blobs...")
            print(f"{'='*60}")
            
            # Run optimizer
            result = optimize_threshold(
                self.loaded_image,
                target_count=target_count,
                material=self.material.currentText(),
                max_blobs=DETECTION_DEFAULTS["max_blobs"],
                clahe_clip=self.active_params.clahe_clip,
                tophat_kernel=self.active_params.tophat_kernel,
                median_kernel=self.active_params.median_kernel,
                min_diam=self.active_params.min_diam,
                max_diam=self.active_params.max_diam,
                morph_iter=self.active_params.morph_iter
            )
            
            # Update parameters with optimized threshold
            self.active_params.threshold = result['threshold']
            
            print(f"\n✓ Optimization complete!")
            print(f"  Optimal threshold: {result['threshold']}")
            print(f"  Blobs detected: {result['blob_count']}")
            print(f"  Exact match: {result['exact_match']}")
            print(f"\nParameters updated:")
            print(self.active_params)
            
        except Exception as e:
            import traceback
            print(f"ERROR during auto-optimization: {e}")
            traceback.print_exc()

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

    def select_roi(self):
        """Select Region of Interest."""
        try:
            if self.loaded_image is None:
                print("No image loaded. Please load a CZI file first.")
                return
            
            print("\n" + "="*60)
            print("REGION OF INTEREST SELECTION")
            print("="*60)
            
            from core.roi import select_roi
            self.roi = select_roi(self.loaded_image)
            
            if self.roi:
                self._update_roi_label()
                print(f"✓ ROI selected: {self.roi}")
            else:
                print("ROI selection cancelled")
                
        except Exception as e:
            import traceback
            print(f"ERROR selecting ROI: {e}")
            traceback.print_exc()
    
    def save_roi(self):
        """Save current ROI to file."""
        try:
            if self.roi is None:
                print("No ROI selected. Please select ROI first.")
                return
            
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save ROI",
                "",
                "JSON Files (*.json)"
            )
            if path:
                save_roi(self.roi, path)
                print(f"✓ ROI saved to {path}")
        except Exception as e:
            import traceback
            print(f"ERROR saving ROI: {e}")
            traceback.print_exc()
    
    def load_roi(self):
        """Load ROI from file."""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Load ROI",
                "",
                "JSON Files (*.json)"
            )
            if path:
                self.roi = load_roi(path)
                self._update_roi_label()
                print(f"✓ ROI loaded: {self.roi}")
        except Exception as e:
            import traceback
            print(f"ERROR loading ROI: {e}")
            traceback.print_exc()
    
    def clear_roi(self):
        """Clear current ROI selection."""
        self.roi = None
        self._update_roi_label()
        print("ROI cleared")
    
    def _update_roi_label(self):
        """Update ROI label display."""
        if self.roi:
            self.roi_label.setText(f"ROI: {self.roi.width}x{self.roi.height}px at ({self.roi.x1}, {self.roi.y1})")
        else:
            self.roi_label.setText("ROI: Not selected")
    def run(self):
        try:
            if self.loaded_image is None or self.loaded_path is None:
                print("No image loaded. Please load a CZI file first.")
                return
            
            # Determine which image to analyze
            analysis_image = self.loaded_image
            if self.roi:
                print(f"\n✓ Applying ROI: {self.roi}")
                analysis_image = self.roi.crop_image(self.loaded_image)
                print(f"  Cropped image: {analysis_image.shape}")

            # If blobs were tuned, use them directly
            if self.tuned_blobs is not None:
                print("\n" + "="*60)
                print("ANALYSIS - Using tuned blobs")
                print("="*60)
                
                reviewed_blobs = self.tuned_blobs
                
                # Calculate statistics on blobs
                if reviewed_blobs:
                    from core.statistics import compute_statistics
                    pixel_size = io.get_pixel_size_um(self.loaded_path)
                    stats = compute_statistics(reviewed_blobs, pixel_size)
                    self.last_stats = {
                        'stats': stats,
                        'blobs': reviewed_blobs,
                        'pixel_size': pixel_size,
                        'roi': self.roi,
                        'params': self.active_params,
                        'material': self.material.currentText(),
                    }
                    
                    print(f"\n✓ Analysis complete!")
                    print(f"  Blobs analyzed: {len(reviewed_blobs)}")
                    print(f"  Mean diameter: {stats['mean']:.2f} µm")
                    print(f"  Std deviation: {stats['std']:.2f} µm")
                    print(f"  CV: {stats['cv']:.2f}%")
                else:
                    self.last_stats = None
                    print(f"\n✓ Analysis complete!")
                    print(f"  No blobs selected for analysis")
                
                return

            # Otherwise, run full analysis pipeline
            print("\n" + "="*60)
            print("ANALYSIS - Full pipeline")
            print("="*60)
            
            # Prepare parameters
            params_dict = {
                "clahe_clip": self.active_params.clahe_clip,
                "tophat_kernel": self.active_params.tophat_kernel,
                "median_kernel": self.active_params.median_kernel,
                "threshold": self.active_params.threshold,
                "morph_iter": self.active_params.morph_iter,
                "min_diam": self.active_params.min_diam,
                "max_diam": self.active_params.max_diam,
            }

            # Run analysis
            print("Running analysis...")
            sys.stdout.flush()
            
            from analysis_worker import run_analysis
            
            result = run_analysis(
                self.loaded_path,
                self.material.currentText(),
                params_dict,
                enable_review=False  # Already handled during tuning
            )
            
            if result["success"]:
                print(f"\n✓ Analysis complete!")
                if result.get("statistics"):
                    stats = result["statistics"]
                    self.last_stats = {
                        'stats': stats,
                        'blobs': result.get('blobs', []),
                        'pixel_size': io.get_pixel_size_um(self.loaded_path),
                        'roi': self.roi,
                        'params': self.active_params,
                        'material': self.material.currentText(),
                    }
                    print(f"  Blobs detected: {stats['count']}")
                    print(f"  Mean diameter: {stats['mean']:.2f} µm")
                    print(f"  CV: {stats['cv']:.2f}%")
                else:
                    self.last_stats = None
                    print(f"  No blobs detected")
            else:
                self.last_stats = None
                print(f"\n✗ Analysis failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            import traceback
            print("\n" + "="*60)
            print(f"✗ ERROR: {e}")
            print("="*60)
            traceback.print_exc()
    def save_results(self):
        """Save analysis results to JSON and CSV files."""
        if self.last_stats is None:
            print("✗ No analysis results to save. Run analysis first.")
            return
        
        try:
            from PySide6.QtWidgets import QFileDialog
            import json
            import csv
            from pathlib import Path
            
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Results", "", "JSON Files (*.json)"
            )
            
            if not file_path:
                return
            
            file_path = Path(file_path)
            
            # Prepare results data
            data = {
                "file": str(self.loaded_path),
                "material": self.last_stats['material'],
                "statistics": {
                    "count": self.last_stats['stats']['count'],
                    "mean_diameter_um": round(self.last_stats['stats']['mean'], 3),
                    "std_deviation_um": round(self.last_stats['stats']['std'], 3),
                    "cv_percent": round(self.last_stats['stats']['cv'], 2),
                },
                "parameters": {
                    "clahe_clip": self.last_stats['params'].clahe_clip,
                    "tophat_kernel": self.last_stats['params'].tophat_kernel,
                    "median_kernel": self.last_stats['params'].median_kernel,
                    "threshold": self.last_stats['params'].threshold,
                    "morph_iter": self.last_stats['params'].morph_iter,
                    "min_diam": self.last_stats['params'].min_diam,
                    "max_diam": self.last_stats['params'].max_diam,
                },
            }
            
            # Add ROI info if available
            if self.last_stats['roi']:
                data["roi"] = {
                    "x1": self.last_stats['roi'].x1,
                    "y1": self.last_stats['roi'].y1,
                    "x2": self.last_stats['roi'].x2,
                    "y2": self.last_stats['roi'].y2,
                }
            
            # Save JSON
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ Results saved to {file_path}")
            
            # Save CSV with blob details
            csv_path = file_path.with_suffix('.csv')
            if self.last_stats['blobs']:
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Blob', 'Diameter (µm)', 'Area (px²)', 'X', 'Y'])
                    
                    pixel_size = self.last_stats['pixel_size']
                    for i, blob in enumerate(self.last_stats['blobs'], 1):
                        # Handle both dict and object formats
                        if isinstance(blob, dict):
                            diameter_um = blob.get('diameter', 0) * pixel_size
                            area = blob.get('area', 0)
                            center = blob.get('center', (0, 0))
                        else:
                            diameter_um = blob.diameter * pixel_size
                            area = blob.area
                            center = blob.center
                        
                        writer.writerow([
                            i,
                            round(diameter_um, 3),
                            area,
                            round(center[0]),
                            round(center[1]),
                        ])
                
                print(f"✓ Blob details saved to {csv_path}")
            
        except Exception as e:
            import traceback
            print(f"✗ Error saving results: {e}")
            traceback.print_exc()