import numpy as np
import scipy.stats as stats

def compute_stats(diams_um):
    mean = np.mean(diams_um)
    std = np.std(diams_um)
    cv = std / mean * 100 if mean > 0 else 0

    if len(diams_um) > 1:
        ci = stats.t.interval(0.95, len(diams_um)-1,
                              loc=mean, scale=stats.sem(diams_um))
    else:
        ci = (mean, mean)

    return mean, std, cv, ci

def compute_statistics(blobs, pixel_size_um=0.34):
    """
    Compute statistics from detected blobs.
    
    Args:
        blobs: List of blob dictionaries with 'diam_px' key
        pixel_size_um: Pixel size in micrometers (default 0.34 µm)
    
    Returns:
        Dictionary with statistics: mean, std, cv
    """
    if not blobs:
        return {
            'mean': 0,
            'std': 0,
            'cv': 0,
            'count': 0
        }
    
    # Extract diameters in pixels and convert to micrometers
    diams_px = [b['diam_px'] for b in blobs]
    diams_um = np.array(diams_px) * pixel_size_um
    
    # Compute statistics
    mean, std, cv, ci = compute_stats(diams_um)
    
    return {
        'mean': mean,
        'std': std,
        'cv': cv,
        'count': len(blobs)
    }