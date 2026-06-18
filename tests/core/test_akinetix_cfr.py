from unittest.mock import MagicMock
from core.domain.services.akinetix_engine import AkinetixEngine


def test_engine_uses_cfr_for_question_selection():
    mock_cfr = MagicMock()
    mock_cfr.solve_best_question.return_value = ("fine:genre_shonen", 0.95)

    # We need a catalog_service mock
    mock_catalog = MagicMock()

    engine = AkinetixEngine(catalog_service=mock_catalog, cfr_solver=mock_cfr)

    # Simulate a proposal where candidates would be evaluated
    # We need to mock _prepare_classical_data results or candidates
    attributes = ["fine:genre_shonen", "genre:action"]

    # Injecting private data for the test to avoid heavy mocking of all internals
    # But wait, Task 1 says:
    # question, confidence = engine.get_next_question([], {})

    # Let's see if get_next_question exists or if I should add it.
    # Currently it's not in the file I read. I will add it as part of the implementation.

    question, confidence = engine.get_next_question(attributes, {})

    assert question == "fine:genre_shonen"
    assert confidence == 0.95
    mock_cfr.solve_best_question.assert_called_once_with(attributes, {})
