MATERIAL_PRESETS = {
    "glass": {
        "clahe_clip": 2.0,
        "tophat_kernel": 15,
        "median_kernel": 3,
        "invert": False,
        "scratch_removal": False,
    },
    "aluminum": {
        "clahe_clip": 2.0,
        "tophat_kernel": 25,
        "median_kernel": 3,
        "invert": True,
        "scratch_removal": True,
    }
}

DETECTION_DEFAULTS = {
    "threshold": 120,
    "morph_iter": 2,
    "min_diam": 5,
    "max_diam": 200,
    "max_blobs": 8
}
