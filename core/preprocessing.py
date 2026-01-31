import cv2
import numpy as np

def preprocess(img, preset):
    img8 = (img / img.max() * 255).astype(np.uint8)

    if preset["invert"]:
        img8 = cv2.bitwise_not(img8)

    clahe = cv2.createCLAHE(clipLimit=preset["clahe_clip"], tileGridSize=(50, 50))
    img8 = clahe.apply(img8)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (preset["tophat_kernel"], preset["tophat_kernel"])
    )

    img8 = cv2.morphologyEx(img8, cv2.MORPH_BLACKHAT, kernel)
    img8 = cv2.medianBlur(img8, preset["median_kernel"])

    return img8
