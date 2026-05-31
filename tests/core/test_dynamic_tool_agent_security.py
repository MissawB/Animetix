import pytest
import os
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

def test_security_rce_blocked_by_default(tool_agent, mock_engine):
    """
    Vérifie que toute exécution est bloquée par défaut (Désactivation totale de exec).
    """
    code = "def execute_tool(): return 'pwned'"
    mock_engine.generate.return_value = code
    
    res = tool_agent.build_and_execute_tool("Doc", "Task")
    
    assert res["status"] == "security_disabled"
    assert "proposed_code" in res
    assert "désactivée" in res["message"]
