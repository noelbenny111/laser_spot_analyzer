"""
Test script for core image processing and interactive tuner.

Run from project root:
    python test_interactive_tuner.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

from core import io, preprocessing, detection, filtering, statistics
from core.interactive_tuner import InteractiveTuner, DetectionParams
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS


# ---------------- USER INPUT ----------------
# CHANGE THIS to a real CZI file path
TEST_CZI_PATH = r"E:\FZJ\Data_2\Lius method\Glass\140825_CG_Z_0.95\29degreee_20x_middle_z0.95.czi"

MATERIAL = "glass"       # "glass" or "aluminum"
MAX_BLOBS = 8
# -------------------------------------------


def test_imports():
    print("✔ Imports OK")


def test_load_czi():
    img = io.load_czi(TEST_CZI_PATH)
    assert img.ndim == 2, "Image must be 2D after loading"
    assert img.size > 0, "Image is empty"
    print(f"✔ Loaded CZI image with shape {img.shape}")
    return img


def test_preprocessing(img):
    preset = MATERIAL_PRESETS[MATERIAL]
    proc = preprocessing.preprocess(img, preset)

    assert proc.dtype == np.uint8, "Preprocessed image must be uint8"
    assert proc.shape == img.shape, "Shape mismatch after preprocessing"

    print("✔ Preprocessing OK")

    # Visual sanity check
    plt.figure(figsize=(5, 6))
    plt.imshow(proc, cmap="gray")
    plt.title("Preprocessed Image (Sanity Check)")
    plt.axis("off")
    plt.show()

    return proc


def test_detection(proc):
    blobs = detection.detect_blobs(proc, DETECTION_DEFAULTS)
    blobs = filtering.filter_blobs(blobs, DETECTION_DEFAULTS["max_blobs"])

    print(f"✔ Detection ran — found {len(blobs)} blobs")

    # Print blob sizes for debugging
    for i, b in enumerate(blobs):
        print(f"  Blob {i}: diam_px = {b['diam_px']:.2f}")

    return blobs


def test_statistics(blobs):
    if not blobs:
        print("⚠ No blobs — skipping statistics test")
        return

    px_size = 0.34  # dummy value for test
    diam_um = [b["diam_px"] * px_size for b in blobs]

    mean, std, cv, ci = statistics.compute_stats(diam_um)

    print("✔ Statistics:")
    print(f"   Mean = {mean:.2f} µm")
    print(f"   Std  = {std:.2f} µm")
    print(f"   CV   = {cv:.2f} %")
    print(f"   CI   = [{ci[0]:.2f}, {ci[1]:.2f}]")


def test_interactive_tuner(img):
    print("\n🔧 Launching Interactive Tuner...")
    print("→ Adjust sliders, then click 'Accept'")

    tuner = InteractiveTuner(
        img,
        material=MATERIAL,
        max_blobs=MAX_BLOBS
    )

    blobs, params = tuner.run()

    print("\n✔ Interactive tuner finished")
    print(f"  Selected {len(blobs)} blobs")
    print("  Final parameters:")
    print(params)

    return blobs, params


def main():
    print("\n=== TESTING INTERACTIVE TUNER PIPELINE ===\n")

    test_imports()

    img = test_load_czi()
    proc = test_preprocessing(img)
    blobs = test_detection(proc)
    test_statistics(blobs)

    # Interactive test (this opens a GUI)
    test_interactive_tuner(img)

    print("\n✅ ALL TESTS COMPLETED")


if __name__ == "__main__":
    main()
