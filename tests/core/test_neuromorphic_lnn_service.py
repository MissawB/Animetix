import pytest
import numpy as np
from core.domain.services.neuromorphic_lnn_service import LiquidNeuralNetworkService

def test_lnn_simulation_step():
    lnn = LiquidNeuralNetworkService(state_dimension=2, input_dimension=1)
    state = np.zeros(2)
    inputs = np.array([1.0])
    
    next_state = lnn.integrate_rk4(state, inputs, dt=0.01)
    assert next_state.shape == (2,)
    assert not np.array_equal(next_state, state)
