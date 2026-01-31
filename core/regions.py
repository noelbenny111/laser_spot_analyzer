def split_columns(img, deg_start, deg_end, width):
    degrees = list(range(deg_start, deg_end - 1, -1))
    regions = {}

    for i, d in enumerate(degrees):
        x0 = i * width
        x1 = x0 + width
        regions[d] = img[:, x0:x1]

    return regions
# This function splits an image into vertical columns based on specified degree
# ranges and width. Each column corresponds to a specific degree value, and the
# function returns a dictionary mapping degree values to their respective image regions.
# Each region is extracted as a slice of the input image array.