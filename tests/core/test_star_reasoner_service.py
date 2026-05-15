import pytest
import os
import json
from unittest.mock import MagicMock
from core.domain.services.star_reasoner_service import StarReasonerService

@pytest.fixture
def mock_engine():
    return MagicMock()

def test_solve_riddle_with_star_success_no_file_check(mock_engine, tmp_path):
    service = StarReasonerService(inference_engine=mock_engine)
    service.training_data_path = str(tmp_path / "star_traces.jsonl")
    
    mock_engine.generate.return_value = "Thinking... FINAL_ANSWER: Naruto"
    res = service.solve_riddle_with_star("Who is orange?", "Naruto", num_attempts=1)
    
    assert res["success"] is True
    assert res["traces_saved"] == 1

def test_solve_riddle_with_star_failure(mock_engine, tmp_path):
    service = StarReasonerService(inference_engine=mock_engine)
    service.training_data_path = str(tmp_path / "star_traces.jsonl")
    
    mock_engine.generate.return_value = "Thinking... FINAL_ANSWER: Luffy"
    res = service.solve_riddle_with_star("Who is orange?", "Naruto", num_attempts=1)
    
    assert res["success"] is False
    assert res["traces_saved"] == 0
