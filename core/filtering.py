def filter_blobs(blobs, max_blobs):
    blobs = sorted(blobs, key=lambda b: b["diam_px"], reverse=True)
    return blobs[:max_blobs]
# This function filters a list of blob dictionaries to retain only the largest
# blobs