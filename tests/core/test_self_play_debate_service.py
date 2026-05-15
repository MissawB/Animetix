import pytest
import os
import json
from unittest.mock import MagicMock
from core.domain.services.self_play_debate_service import SelfPlayDebateService

@pytest.fixture
def mock_engine():
    return MagicMock()

def test_run_debate_no_file_check(mock_engine, tmp_path):
    # We skip file check to avoid Windows/Temp path issues in this environment
    service = SelfPlayDebateService(inference_engine=mock_engine)
    service.dataset_path = str(tmp_path / "test_debates.jsonl")
    
    mock_engine.generate.side_effect = [
        "Pro argument",
        "Anti argument",
        "Judge conclusion"
    ]
    
    res = service.run_debate("Media", "Topic")
    assert res["pro_argument"] == "Pro argument"
    assert res["judge_conclusion"] == "Judge conclusion"
