import os

from core.domain.services.prompt_manager import PromptManager

PROMPTS_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "backend",
        "core",
        "domain",
        "services",
        "prompts",
    )
)


def test_personality_templates_render_with_memories():
    pm = PromptManager(prompts_dir=PROMPTS_DIR)
    for key in ("sensei_personality", "tsundere_personality", "kuudere_personality"):
        prompt, _ = pm.get_prompt(
            key, user_msg="u", context="c", history="h", memories="MY-MEMORY"
        )
        assert "MY-MEMORY" in prompt, f"{key} did not render the memories slot"
