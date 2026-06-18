import os
from backend.core.domain.services.prompt_manager import PromptManager


def test_prompt_manager_moderator_loading():
    # Path to the prompts directory as specified in the task
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompts_dir = os.path.join(base_dir, "src", "core", "domain", "services", "prompts")

    # Verify the directory exists
    assert os.path.exists(prompts_dir), f"Prompts directory not found at {prompts_dir}"

    manager = PromptManager(prompts_dir)

    # Test input_moderator
    input_prompt, input_system = manager.get_prompt(
        "input_moderator", categories="HATE_SPEECH, JAILBREAK", text="test query"
    )
    assert "Tu es le modérateur d'entrée d'Animetix" in input_system
    assert "HATE_SPEECH, JAILBREAK" in input_system
    assert input_prompt == "test query"

    # Test output_moderator
    output_prompt, output_system = manager.get_prompt(
        "output_moderator", categories="SPOILER", text="test response"
    )
    assert "Tu es le modérateur de sortie d'Animetix" in output_system
    assert "SPOILER" in output_system
    assert output_prompt == "test response"


def test_get_system_prompt_direct():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompts_dir = os.path.join(base_dir, "src", "core", "domain", "services", "prompts")

    manager = PromptManager(prompts_dir)

    system = manager.get_system_prompt("input_moderator", categories="CAT1")
    assert "Tu es le modérateur d'entrée d'Animetix" in system
    assert "CAT1" in system
