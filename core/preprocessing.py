import cv2
import numpy as np

def preprocess(img, preset):
    # Safety check: ensure image is valid
    if img is None or img.size == 0:
        raise ValueError("Invalid image: empty or None")
    
    # Normalize image safely
    img_max = img.max()
    if img_max <= 0:
        print("Warning: Image has no positive values, using fallback normalization")
        img8 = np.clip(img * 255, 0, 255).astype(np.uint8)
    else:
        img8 = (img / img_max * 255).astype(np.uint8)

    if preset["invert"]:
        img8 = cv2.bitwise_not(img8)

    # Use smaller tile size for better performance (8x8 instead of 16x16 for faster interactivity)
    clahe = cv2.createCLAHE(clipLimit=preset["clahe_clip"], tileGridSize=(8, 8))
    img8 = clahe.apply(img8)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (preset["tophat_kernel"], preset["tophat_kernel"])
    )

    img8 = cv2.morphologyEx(img8, cv2.MORPH_BLACKHAT, kernel)
    img8 = cv2.medianBlur(img8, preset["median_kernel"])

    return img8
