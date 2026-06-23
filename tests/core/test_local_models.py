import importlib


def test_canonical_defaults():
    from core.utils import local_models as lm

    assert lm.LLM_OLLAMA_MODEL == "qwen3.5"
    assert lm.LOCAL_TEXT_MODEL == "Qwen/Qwen3.5-4B"
    assert lm.DRAFT_TEXT_MODEL == "Qwen/Qwen2.5-0.5B-Instruct"
    assert lm.COMPACT_REASONING_MODEL == "WeiboAI/VibeThinker-3B"
    assert lm.LOCAL_DIFFUSION_MODEL_ID == "black-forest-labs/FLUX.1-schnell"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_MODEL_NAME", "llm-x")
    monkeypatch.setenv("LOCAL_MODEL_ID", "text-x")
    monkeypatch.setenv("DRAFT_MODEL_ID", "draft-x")
    monkeypatch.setenv("COMPACT_MODEL_ID", "compact-x")
    monkeypatch.setenv("LOCAL_DIFFUSION_MODEL", "diff-x")
    import core.utils.local_models as lm

    lm = importlib.reload(lm)
    assert lm.LLM_OLLAMA_MODEL == "llm-x"
    assert lm.LOCAL_TEXT_MODEL == "text-x"
    assert lm.DRAFT_TEXT_MODEL == "draft-x"
    assert lm.COMPACT_REASONING_MODEL == "compact-x"
    assert lm.LOCAL_DIFFUSION_MODEL_ID == "diff-x"
