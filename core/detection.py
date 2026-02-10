import cv2
import numpy as np

MIN_CONTOUR_AREA = 20

def detect_blobs(img, params):
    try:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morph = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, params["morph_iter"])

        _, th = cv2.threshold(morph, params["threshold"], 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        blobs = []
        for c in contours:
            if cv2.contourArea(c) < MIN_CONTOUR_AREA:
                continue

            try:
                if len(c) >= 5:
                    (x, y), (MA, ma), ang = cv2.fitEllipse(c)
                    d = (MA * ma) ** 0.5
                    ell = ((x, y), (MA, ma), ang)
                else:
                    (x, y), r = cv2.minEnclosingCircle(c)
                    d = 2 * r
                    ell = None

                if params["min_diam"] <= d <= params["max_diam"]:
                    blobs.append({"center": (x, y), "diam_px": d, "ellipse": ell})
            except Exception as e:
                # Skip problematic contours
                print(f"Warning: Could not process contour: {e}")
                continue

        return blobs
    except Exception as e:
        print(f"Error in detect_blobs: {e}")
        raise
