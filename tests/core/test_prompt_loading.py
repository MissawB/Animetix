import os

from core.domain.services.prompt_manager import PromptManager


def test_prompt_manager_moderator_loading():
    # Path to the prompts directory as specified in the task
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompts_dir = os.path.join(
        base_dir, "backend", "core", "domain", "services", "prompts"
    )

    # Verify the directory exists
    assert os.path.exists(prompts_dir), f"Prompts directory not found at {prompts_dir}"

    manager = PromptManager(prompts_dir)

    # Test input_moderator
    input_prompt, input_system = manager.get_prompt(
        "input_moderator", categories="HATE_SPEECH, JAILBREAK", text="test query"
    )
    assert "sentinelle de sécurité" in input_system
    assert "test query" in input_prompt

    # Test output_moderator
    output_prompt, output_system = manager.get_prompt(
        "output_moderator", categories="SPOILER", text="test response"
    )
    assert "auditeur de sortie" in output_system
    assert "test response" in output_prompt


def test_get_system_prompt_direct():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    prompts_dir = os.path.join(
        base_dir, "backend", "core", "domain", "services", "prompts"
    )

    manager = PromptManager(prompts_dir)

    system = manager.get_system_prompt("input_moderator", categories="CAT1")
    assert "sentinelle de sécurité" in system
