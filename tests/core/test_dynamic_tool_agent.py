import pytest
from unittest.mock import MagicMock
from core.domain.services.dynamic_tool_agent import DynamicToolAgent

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def tool_agent(mock_engine):
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    return DynamicToolAgent(inference_engine=mock_engine, prompt_manager=mock_pm)

def test_build_and_execute_tool_success(tool_agent, mock_engine):
    # Mock LLM generating correct Python code
    code = """
import requests
def execute_tool():
    return {"result": "success"}
"""
    mock_engine.generate.return_value = code
    
    res = tool_agent.build_and_execute_tool("API Doc", "Get data")
    assert res["status"] == "success"
    assert res["data"] == {"result": "success"}

def test_build_and_execute_tool_markdown_cleanup(tool_agent, mock_engine):
    code = "```python\ndef execute_tool(): return {'ok': True}\n```"
    mock_engine.generate.return_value = code
    res = tool_agent.build_and_execute_tool("Doc", "Task")
    assert res["status"] == "success"
    assert res["data"] == {'ok': True}

def test_build_and_execute_tool_invalid_code(tool_agent, mock_engine):
    mock_engine.generate.return_value = "This is not python code at all."
    res = tool_agent.build_and_execute_tool("Doc", "Task")
    assert res["status"] == "error"
    assert "error" in res

def test_build_and_execute_tool_missing_function(tool_agent, mock_engine):
    mock_engine.generate.return_value = "def wrong_name(): pass"
    res = tool_agent.build_and_execute_tool("Doc", "Task")
    assert res["status"] == "error"
    assert "not defined" in res["error"]
