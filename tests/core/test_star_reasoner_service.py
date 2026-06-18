from unittest.mock import MagicMock

import pytest
from core.domain.services.star_reasoner_service import StarReasonerService


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def mock_prompt_manager():
    pm = MagicMock()
    pm.get_prompt.return_value = ("formatted prompt", "system prompt")
    return pm


@pytest.fixture
def mock_gold_dataset_port():
    return MagicMock()


def test_solve_riddle_with_star_success(
    mock_engine, mock_prompt_manager, mock_gold_dataset_port, tmp_path
):
    # Use a temporary file path for testing
    trace_file = tmp_path / "star_traces.jsonl"
    service = StarReasonerService(
        inference_engine=mock_engine,
        prompt_manager=mock_prompt_manager,
        gold_dataset_port=mock_gold_dataset_port,
    )
    service.training_data_path = str(trace_file)

    mock_engine.generate.return_value = "Step 1... Step 2... FINAL_ANSWER: Naruto"
    res = service.solve_riddle_with_star("Who is orange?", "Naruto", num_attempts=1)

    assert res["success"] is True
    assert res["traces_saved"] == 1
    assert "Naruto" in res["best_response"]

    mock_gold_dataset_port.save_star_trace.assert_called_once()


def test_solve_riddle_with_star_partial_success(
    mock_engine, mock_prompt_manager, mock_gold_dataset_port, tmp_path
):
    trace_file = tmp_path / "star_traces_partial.jsonl"
    service = StarReasonerService(
        inference_engine=mock_engine,
        prompt_manager=mock_prompt_manager,
        gold_dataset_port=mock_gold_dataset_port,
    )
    service.training_data_path = str(trace_file)

    # First fail, then succeed
    mock_engine.generate.side_effect = [
        "Thinking... FINAL_ANSWER: Luffy",
        "Thinking... FINAL_ANSWER: Naruto Uzumaki",
    ]

    res = service.solve_riddle_with_star("Who is orange?", "Naruto", num_attempts=2)

    assert res["success"] is True
    assert res["traces_saved"] == 1
    assert "Naruto Uzumaki" in res["best_response"]

    mock_gold_dataset_port.save_star_trace.assert_called_once()


def test_solve_riddle_with_star_no_tag(
    mock_engine, mock_prompt_manager, mock_gold_dataset_port, tmp_path
):
    service = StarReasonerService(
        inference_engine=mock_engine,
        prompt_manager=mock_prompt_manager,
        gold_dataset_port=mock_gold_dataset_port,
    )
    mock_engine.generate.return_value = "The answer is Naruto but I forgot the tag."

    res = service.solve_riddle_with_star("Who is orange?", "Naruto", num_attempts=1)

    # Expected behavior: without FINAL_ANSWER tag, it might fail depending on expected_answer check
    # But current implementation checks 'expected_answer in final_answer', and final_answer is empty here.
    assert res["success"] is False
    mock_gold_dataset_port.save_star_trace.assert_not_called()


def test_solve_riddle_with_star_engine_error(
    mock_engine, mock_prompt_manager, mock_gold_dataset_port, tmp_path
):
    service = StarReasonerService(
        inference_engine=mock_engine,
        prompt_manager=mock_prompt_manager,
        gold_dataset_port=mock_gold_dataset_port,
    )
    mock_engine.generate.return_value = ""  # Empty engine response

    res = service.solve_riddle_with_star("Test", "Test", num_attempts=1)
    assert res["success"] is False
    assert res["traces_saved"] == 0
    mock_gold_dataset_port.save_star_trace.assert_not_called()
