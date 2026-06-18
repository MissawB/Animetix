from unittest.mock import MagicMock

import pytest
from core.domain.services.dynamic_tool_agent import DynamicToolAgent


@pytest.fixture
def mock_engine():
    return MagicMock()


@pytest.fixture
def tool_agent(mock_engine):
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    return DynamicToolAgent(inference_engine=mock_engine, prompt_manager=mock_pm)


def test_build_and_execute_tool_security_disabled(tool_agent, mock_engine):
    # Mock LLM generating correct Python code
    code = """
def execute_tool():
    return {"result": "success"}
"""
    mock_engine.generate.return_value = code

    res = tool_agent.build_and_execute_tool("API Doc", "Get data")
    assert res["status"] == "security_disabled"
    assert "proposed_code" in res
    assert "désactivée" in res["message"]
