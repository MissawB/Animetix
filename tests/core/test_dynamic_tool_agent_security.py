import pytest
import os
import ast
from unittest.mock import MagicMock
from core.domain.services.dynamic_tool_agent import DynamicToolAgent, CodeSafetyValidator

@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def tool_agent(mock_engine):
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    return DynamicToolAgent(inference_engine=mock_engine, prompt_manager=mock_pm)

def test_security_rce_blocked(tool_agent, mock_engine):
    """
    Test that attempts RCE and verifies it's blocked.
    """
    # Create a marker file to test if RCE succeeds
    marker_file = "rce_marker.txt"
    if os.path.exists(marker_file):
        os.remove(marker_file)
        
    # Malicious code attempting to write a file to disk using 'open'
    malicious_code = f"""
def execute_tool():
    with open("{marker_file}", "w") as f:
        f.write("RCE SUCCESSFUL")
    return "pwned"
"""
    mock_engine.generate.return_value = malicious_code
    
    res = tool_agent.build_and_execute_tool("Doc", "Malicious Task")
    
    # Check if marker file was created
    rce_success = os.path.exists(marker_file)
    if rce_success:
        os.remove(marker_file)
        
    assert not rce_success, "RCE was successful! Marker file created."
    assert res["status"] == "error"
    assert "Security Violation" in res["error"] or "interdit" in res["error"] or "forbidden" in res["error"]

def test_code_safety_validator_blocks_private_attributes():
    validator = CodeSafetyValidator()
    # Test double underscore
    code = "obj.__class__"
    tree = ast.parse(code)
    validator.visit(tree)
    assert any("interdit" in err or "forbidden" in err or "Violation" in err for err in validator.errors)
    
    # Test single underscore
    validator.errors = []
    code = "obj._hidden_attr"
    tree = ast.parse(code)
    validator.visit(tree)
    assert any("interdit" in err or "forbidden" in err or "Violation" in err for err in validator.errors)

def test_code_safety_validator_blocks_internal_names():
    validator = CodeSafetyValidator()
    # Test __globals__ access
    code = "print(__globals__)"
    tree = ast.parse(code)
    validator.visit(tree)
    assert any("interdit" in err or "forbidden" in err or "Violation" in err for err in validator.errors)

def test_dynamic_tool_agent_rejects_malicious_code_subclasses():
    mock_engine = MagicMock()
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    agent = DynamicToolAgent(inference_engine=mock_engine, prompt_manager=mock_pm)
    
    # Malicious code attempting to access __subclasses__
    malicious_code = """
def execute_tool():
    return [].__class__.__base__.__subclasses__()
"""
    mock_engine.generate.return_value = malicious_code
    
    res = agent.build_and_execute_tool("doc", "task")
    assert res["status"] == "error"
    assert "Security Violation" in res["error"] or "interdit" in res["error"]

def test_dynamic_tool_agent_rejects_private_access():
    mock_engine = MagicMock()
    mock_pm = MagicMock()
    mock_pm.get_prompt.return_value = ("prompt", "system")
    agent = DynamicToolAgent(inference_engine=mock_engine, prompt_manager=mock_pm)
    
    # Malicious code attempting to access _module_name
    malicious_code = """
import requests
def execute_tool():
    return requests._utils
"""
    mock_engine.generate.return_value = malicious_code
    
    res = agent.build_and_execute_tool("doc", "task")
    assert res["status"] == "error"
    assert "Security Violation" in res["error"] or "interdit" in res["error"]
