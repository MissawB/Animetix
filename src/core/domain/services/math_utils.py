import numpy as np

def get_gaussian_weights(n: int) -> list[float]:
    """
    Calculates gaussian weights for a sequence of length n.
    Pure domain logic for similarity weighting.
    """
    if n <= 0:
        return []
    mu = n * 0.4
    sigma = n * 0.8
    x = np.arange(n)
    weights = np.exp(-0.5 * ((x - mu) / sigma)**2)
    return weights.tolist()
