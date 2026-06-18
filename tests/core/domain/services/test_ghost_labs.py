import numpy as np
from backend.core.domain.services.neuromorphic_lnn_service import (
    LiquidNeuralNetworkService,
)
from backend.core.domain.services.neuromorphic_plasticity_service import (
    SynapticPlasticityService,
)
from backend.core.domain.services.quantum_cognitive_service import (
    QuantumCognitiveService,
)

# --- LNN TESTS ---


def test_lnn_initialization():
    service = LiquidNeuralNetworkService(state_dimension=4, input_dimension=2)
    assert service.state.shape == (4,)
    assert service.W.shape == (4, 4)
    assert service.I_W.shape == (4, 2)
    assert service.tau.shape == (4,)


def test_lnn_processing():
    service = LiquidNeuralNetworkService(state_dimension=4, input_dimension=2)
    input_signal = [[0.5, 0.2], [0.6, 0.1], [0.4, 0.3]]
    history = service.process_continuous_signal(input_signal, dt=0.01)

    assert len(history) == 3
    assert len(history[0]) == 4
    # Check that state changed
    assert not np.allclose(service.state, np.zeros(4))


def test_lnn_stability_reset():
    service = LiquidNeuralNetworkService()
    # Force an invalid state
    service.state[0] = np.nan
    input_signal = [[0.1, 0.1]]
    service.process_continuous_signal(input_signal)
    # Service should have reset the state to zeros after detecting NaN
    assert not np.any(np.isnan(service.state))


def test_lnn_serialization():
    service = LiquidNeuralNetworkService()
    service.process_continuous_signal([[0.1, 0.2]])
    data = service.to_dict()

    new_service = LiquidNeuralNetworkService.from_dict(data)
    assert np.allclose(service.state, new_service.state)
    assert np.allclose(service.W, new_service.W)


# --- PLASTICITY TESTS ---


def test_plasticity_hebbian():
    service = SynapticPlasticityService(num_concepts=5)
    activations = [0.8, 0.0, 0.8, 0.0, 0.0]
    old_w = np.copy(service.W)
    service.update_hebbian(activations)

    # Connection between concept 0 and 2 should increase
    assert service.W[0, 2] > old_w[0, 2]
    # Diagonals should remain 0
    assert service.W[0, 0] == 0.0


def test_plasticity_stdp():
    service = SynapticPlasticityService(num_concepts=5)
    # Pre-synaptic fires at t=10, Post-synaptic fires at t=15 (LTP)
    service.trigger_spikes([0], 10.0)
    service.trigger_spikes([1], 15.0)

    old_w = service.W[0, 1]
    service.update_stdp(0, 1)
    assert service.W[0, 1] > old_w

    # Pre-synaptic fires at t=25, Post-synaptic fired at t=20 (LTD)
    service.trigger_spikes([2], 25.0)
    service.trigger_spikes([3], 20.0)

    old_w_ltd = service.W[2, 3]
    service.update_stdp(2, 3)
    assert service.W[2, 3] < old_w_ltd


def test_plasticity_serialization():
    service = SynapticPlasticityService(num_concepts=3)
    service.update_hebbian([1.0, 1.0, 0.0])
    data = service.to_dict()

    new_service = SynapticPlasticityService.from_dict(data)
    assert np.allclose(service.W, new_service.W)


# --- QUANTUM COGNITION TESTS ---


def test_quantum_born_rule():
    service = QuantumCognitiveService()
    # Measure Shonen
    prob, outcome = service.measure_preference("shonen")
    assert 0.0 <= prob <= 1.0
    assert isinstance(outcome, bool)
    # State should be normalized
    assert np.isclose(np.linalg.norm(service.state), 1.0)


def test_quantum_order_effects():
    service = QuantumCognitiveService()
    # In Quantum Cognition, P(A then B) != P(B then A) usually
    p1, p2 = service.order_effects_demonstration("shonen", "ghibli")
    # In our specific vectors, these should differ
    assert p1 != p2


def test_quantum_serialization():
    service = QuantumCognitiveService()
    service.measure_preference("shonen")
    data = service.to_dict()

    new_service = QuantumCognitiveService.from_dict(data)
    assert np.allclose(service.state, new_service.state)
