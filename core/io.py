import numpy as np
import czifile
from aicspylibczi import CziFile
import cv2
import pandas as pd

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
    try:
        czi = CziFile(path)
        for e in czi.meta.iter():
            if e.tag.endswith("Distance") and e.attrib.get("Id", "").upper() == "X":
                return float(e.find("./Value").text) * 1e6
    except Exception:
        pass
    return 0.34  # fallback

def save_image(path, img):
    cv2.imwrite(path, img)

def save_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)
