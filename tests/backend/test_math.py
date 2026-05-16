import pytest
from src.core.domain.services.math_utils import get_gaussian_weights

def test_get_gaussian_weights_length():
    weights = get_gaussian_weights(10)
    assert len(weights) == 10
    assert all(isinstance(w, float) for w in weights)

def test_get_gaussian_weights_values():
    weights = get_gaussian_weights(5)
    # The middle weights should be higher than the edges (gaussian curve)
    # mu = 5 * 0.4 = 2.0. So weights[2] should be the highest.
    assert weights[2] > weights[0]
    assert weights[2] > weights[4]

def test_get_gaussian_weights_empty():
    assert get_gaussian_weights(0) == []
    assert get_gaussian_weights(-5) == []
