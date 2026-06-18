import pytest
from unittest.mock import MagicMock
from core.domain.services.neuro_symbolic_service import NeuroSymbolicService
from core.domain.services.neuro_symbolic.formal_solver import FormalLogicSolver


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("formatted prompt", "system prompt")
    return pm


@pytest.fixture
def neuro_service(mock_engine, mock_prompt_manager):
    return NeuroSymbolicService(
        inference_engine=mock_engine, prompt_manager=mock_prompt_manager
    )


def test_solve_paradox_success(neuro_service, mock_engine):
    # Setup mocks
    mock_engine.generate.side_effect = [
        '{"A": {"p": true}, "B": {"p": true}, "C": {"p": false}}',  # Step 1
        "The explanation.",  # Step 3
    ]

    neuro_service.solver = MagicMock()
    neuro_service.solver.find_intruder.return_value = ("C", "Proof C", {})

    intruder, explanation, meta = neuro_service.solve_paradox("Anime", "A", "B", "C")
    assert intruder == "C"
    assert explanation == "The explanation."


def test_formal_logic_solver_mock_fallback():
    solver = FormalLogicSolver()
    items = ["A", "B", "Z"]
    properties = {"A": {"p": True}, "B": {"p": True}, "Z": {"p": False}}
    # Test internal _mock_solver
    intruder, proof = solver._mock_solver(items, properties)
    assert intruder == "Z"
    assert "differs on 'p'" in proof


def test_formal_logic_solver_fail():
    solver = FormalLogicSolver()
    items = ["A", "B", "C"]
    properties = {"A": {"p": True}, "B": {"p": True}, "C": {"p": True}}
    intruder, proof = solver._mock_solver(items, properties)
    assert intruder is None
