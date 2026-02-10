import numpy as np
import czifile
import cv2
import pandas as pd
import xml.etree.ElementTree as ET

# Cache for pixel sizes to avoid re-parsing metadata
_pixel_size_cache = {}

def load_czi(path):
    arr = czifile.imread(path)
    arr = np.squeeze(arr)

    if arr.ndim == 2:
        return arr.astype(np.float32)

    if arr.ndim == 3 and arr.shape[-1] == 3:
        weights = np.array([0.2989, 0.5870, 0.1140])
        return np.dot(arr[..., :3], weights).astype(np.float32)

    return arr[..., 0].astype(np.float32)

def get_pixel_size_um(path):
    # Return cached value if available
    if path in _pixel_size_cache:
        return _pixel_size_cache[path]
    
    result = 0.34  # default fallback
    
    try:
        # Try to extract pixel size from CZI metadata using czifile
        with czifile.CziFile(path) as czi:
            # Get metadata as XML
            metadata = czi.metadata()
            if metadata is not None:
                # Parse XML metadata
                root = ET.fromstring(metadata)
                
                # Look for pixel scale in metadata
                # CZI files typically store this in /Metadata/Scaling/Items/Distance
                namespaces = {
                    'czi': 'http://www.zeiss.com/czi/xml/metadata'
                }
                
                # Try to find Distance element with Id="X"
                for distance in root.findall('.//czi:Distance[@Id="X"]', namespaces):
                    value = distance.find('czi:Value', namespaces)
                    if value is not None and value.text:
                        try:
                            result = float(value.text) * 1e6  # Convert to µm
                            print(f"✓ Pixel size from CZI: {result:.4f} µm")
                        except (ValueError, TypeError):
                            pass
                
                # If not found with namespace, try without namespace
                if result == 0.34:
                    for distance in root.findall('.//Distance[@Id="X"]'):
                        value = distance.find('Value')
                        if value is not None and value.text:
                            try:
                                result = float(value.text) * 1e6
                                print(f"✓ Pixel size from CZI: {result:.4f} µm")
                                break
                            except (ValueError, TypeError):
                                pass
                                
    except Exception as e:
        print(f"Note: Using default pixel size (0.34 µm) - could not extract from file: {e}")
    
    _pixel_size_cache[path] = result
    return result

def save_image(path, img):
    cv2.imwrite(path, img)

def save_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
