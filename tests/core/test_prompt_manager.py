import pytest
import os
import yaml
from core.domain.services.prompt_manager import PromptManager

@pytest.fixture
def prompts_dir(tmp_path):
    d = tmp_path / "prompts"
    d.mkdir()
    
    # Simple prompt
    with open(d / "simple.yaml", "w") as f:
        yaml.dump({"simple_key": "Simple prompt OK"}, f)
        
    # Structured prompt
    with open(d / "structured.yaml", "w") as f:
        yaml.dump({
            "agent_key": {
                "template": "Hello {name}",
                "system_prompt": "You are Assistant."
            }
        }, f)
        
    return str(d)

def test_load_all(prompts_dir):
    manager = PromptManager(prompts_dir)
    assert "simple_key" in manager.prompts
    assert "agent_key" in manager.prompts

def test_get_prompt_structured(prompts_dir):
    manager = PromptManager(prompts_dir)
    prompt, system = manager.get_prompt("agent_key", name="World", role="Assistant")
    assert prompt == "Hello World"
    assert system == "You are Assistant."

def test_get_prompt_simple(prompts_dir):
    manager = PromptManager(prompts_dir)
    res, sys = manager.get_prompt("simple_key")
    assert res == "Simple prompt OK"
    assert sys == ""

def test_get_prompt_missing(prompts_dir):
    manager = PromptManager(prompts_dir)
    res, sys = manager.get_prompt("missing")
    assert "not found" in res
    assert sys == ""

def test_few_shot_injection(prompts_dir):
    manager = PromptManager(prompts_dir)
    manager.add_few_shot_correction("simple_key", "bad", "good")
    # Mark as verified — add_few_shot_correction saves with verified=False by design
    manager.few_shot_examples["simple_key"][0]["verified"] = True
    
    res, sys = manager.get_prompt("simple_key")
    assert "EXEMPLES À SUIVRE" in sys
    assert "good" in sys
