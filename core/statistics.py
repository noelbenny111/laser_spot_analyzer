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
