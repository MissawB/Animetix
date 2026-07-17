import json
import os

import pytest
from core.domain.services.self_play_debate_service import SelfPlayDebateService


def test_run_debate_full_flow(mock_engine, mock_prompt_manager, tmp_path):
    debate_file = tmp_path / "debates.jsonl"
    mock_engine.prompt_manager = mock_prompt_manager
    service = SelfPlayDebateService(llm_service=mock_engine)
    service.dataset_path = str(debate_file)

    mock_engine.generate.side_effect = [
        "Pro: This anime is a masterpiece of character development.",
        "Anti: Actually, the pacing is slow and characters are tropes.",
        "Judge: While the development is strong, the pacing indeed has issues. Overall good.",
    ]

    res = service.run_debate("Death Note", "Moral ambiguity")

    assert res["media"] == "Death Note"
    assert "masterpiece" in res["pro_argument"]
    assert "tropes" in res["anti_argument"]
    assert "overall good" in res["judge_conclusion"].lower()

    # Check DPO format saving
    assert os.path.exists(debate_file)
    with open(debate_file, "r") as f:
        data = json.loads(f.readline())
        assert data["chosen"] == res["judge_conclusion"]
        assert data["rejected"] == res["anti_argument"]


def test_run_debate_with_engine_failure(mock_engine, mock_prompt_manager, tmp_path):
    mock_engine.prompt_manager = mock_prompt_manager
    service = SelfPlayDebateService(llm_service=mock_engine)
    # Simulate first call working, second failing
    mock_engine.generate.side_effect = [
        "Pro argument",
        Exception("Inference Timeout"),
        "Judge conclusion",
    ]

    with pytest.raises(Exception) as excinfo:
        service.run_debate("One Piece", "Length")

    assert "Inference Timeout" in str(excinfo.value)
