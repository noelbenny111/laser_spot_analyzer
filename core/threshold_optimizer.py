"""
Target Count Optimizer - Automatically finds the optimal threshold
to detect a specific number of blobs.
"""

import numpy as np
from core.preprocessing import preprocess
from core.detection import detect_blobs
from core.filtering import filter_blobs
from config import MATERIAL_PRESETS, DETECTION_DEFAULTS


def optimize_threshold(img, target_count, material="glass", max_blobs=8, 
                       min_diam=5, max_diam=200, morph_iter=2,
                       clahe_clip=2.0, tophat_kernel=15, median_kernel=3,
                       callback=None):
    """
    Automatically find the optimal threshold to detect target_count blobs.
    
    Args:
        img: Image array
        target_count: Desired number of blobs to detect
        material: "glass" or "aluminum"
        max_blobs: Maximum blobs to consider
        min_diam, max_diam: Size constraints
        morph_iter, clahe_clip, tophat_kernel, median_kernel: Processing parameters
        callback: Function to call with progress updates: callback(threshold, count, status)
    
    Returns:
        dict with keys: 'threshold', 'blob_count', 'blobs', 'history'
    """
    
    print(f"\n{'='*60}")
    print(f"TARGET COUNT OPTIMIZER - Finding threshold for {target_count} blobs")
    print(f"{'='*60}\n")
    
    # Preset for preprocessing
    preset = MATERIAL_PRESETS[material].copy()
    preset["clahe_clip"] = clahe_clip
    preset["tophat_kernel"] = tophat_kernel
    preset["median_kernel"] = median_kernel
    
    # Try different thresholds using binary search
    best_threshold = 128
    best_count = 0
    best_blobs = []
    history = []
    
    # Binary search bounds
    min_threshold = 1
    max_threshold = 255
    iterations = 0
    max_iterations = 12  # log2(256) ≈ 8, plus some buffer
    
    while iterations < max_iterations:
        iterations += 1
        mid_threshold = (min_threshold + max_threshold) // 2
        
        # Process image with this threshold
        proc = preprocess(img, preset)
        
        blobs = detect_blobs(proc, {
            **DETECTION_DEFAULTS,
            "threshold": mid_threshold,
            "morph_iter": morph_iter,
            "min_diam": min_diam,
            "max_diam": max_diam,
        })
        
        blobs = filter_blobs(blobs, max_blobs)
        blob_count = len(blobs)
        
        # Record history
        history_entry = {
            'threshold': mid_threshold,
            'count': blob_count,
            'distance': abs(blob_count - target_count)
        }
        history.append(history_entry)
        
        print(f"Iteration {iterations:2d} | Threshold: {mid_threshold:3d} | Blobs: {blob_count:2d} | Target: {target_count} | Distance: {abs(blob_count - target_count)}")
        
        # Update callback if provided
        if callback:
            status = "Exact match!" if blob_count == target_count else "Searching..."
            callback(mid_threshold, blob_count, status)
        
        # Track best result
        if abs(blob_count - target_count) < abs(best_count - target_count):
            best_count = blob_count
            best_threshold = mid_threshold
            best_blobs = blobs
        
        # Check if we found the exact count
        if blob_count == target_count:
            print(f"\n✓ FOUND! Threshold {mid_threshold} detects exactly {target_count} blobs")
            break
        
        # Adjust search range using binary search logic
        if blob_count < target_count:
            # Too few blobs - lower the threshold to detect more
            max_threshold = mid_threshold - 1
        else:
            # Too many blobs - raise the threshold to detect fewer
            min_threshold = mid_threshold + 1
        
        # Stop if search range is exhausted
        if min_threshold > max_threshold:
            print(f"\n⚠ Search complete. Best match: Threshold {best_threshold} detects {best_count} blobs (target: {target_count})")
            break
    
    print(f"\n{'='*60}")
    print(f"Result: Threshold = {best_threshold}, Blobs detected = {best_count}")
    print(f"{'='*60}\n")
    
    return {
        'threshold': best_threshold,
        'blob_count': best_count,
        'blobs': best_blobs,
        'history': history,
        'exact_match': best_count == target_count
    }


if __name__ == "__main__":
    # Test example
    from core import io
    
    img = io.load_czi(r"E:\FZJ\Data_2\Lius method\Glass\140825_CG_Z_0.95\29degreee_20x_middle_z0.95.czi")
    
    # Find threshold for 4 blobs
    result = optimize_threshold(img, target_count=4, material="glass")
    
    print(f"\nFinal result: threshold={result['threshold']}, blobs={result['blob_count']}")
    print(f"Exact match: {result['exact_match']}")
