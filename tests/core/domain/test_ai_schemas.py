import pytest
from pydantic import ValidationError
from backend.core.domain.entities.ai_schemas import (
    InferenceResponse,
    InferenceMetadata,
    TokenLogProb,
    RAGContext,
    CombatCharacter,
    CombatStats,
)


def test_token_logprob_schema():
    """Test individual TokenLogProb instantiation and validation."""
    logprob = TokenLogProb(token="Naruto", logprob=-0.5)
    assert logprob.token == "Naruto"
    assert logprob.logprob == -0.5
    assert logprob.top_logprobs is None

    # Test with top_logprobs
    logprob_rich = TokenLogProb(
        token="Sasuke", logprob=-0.1, top_logprobs=[{"Sasuke": -0.1, "Sakura": -2.5}]
    )
    assert len(logprob_rich.top_logprobs) == 1
    assert logprob_rich.top_logprobs[0]["Sakura"] == -2.5


def test_inference_metadata_defaults():
    """Test InferenceMetadata default values."""
    meta = InferenceMetadata()
    assert meta.logprobs is None
    assert meta.usage is None
    assert meta.thinking is None
    assert meta.diagnostics is None


def test_inference_response_complex():
    """Test complex InferenceResponse with full metadata."""
    res = InferenceResponse(
        text="Bankai!",
        metadata=InferenceMetadata(
            logprobs=[TokenLogProb(token="Bankai", logprob=-0.001)],
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            thinking="The user wants a cool anime shout.",
            diagnostics={"latency_ms": 150},
        ),
    )
    assert res.text == "Bankai!"
    assert res.metadata.usage["prompt_tokens"] == 10
    assert res.metadata.diagnostics["latency_ms"] == 150
    assert res.metadata.logprobs[0].token == "Bankai"


def test_inference_response_default_metadata():
    """Test that InferenceResponse creates empty metadata by default."""
    res = InferenceResponse(text="Hello")
    assert isinstance(res.metadata, InferenceMetadata)
    assert res.metadata.logprobs is None


def test_rag_context_config():
    """Verify RAGContext arbitrary_types_allowed works via ConfigDict."""
    # RAGContext uses Any for graph_expert, which usually doesn't need arbitrary_types_allowed
    # but we want to ensure the config is correctly applied.
    ctx = RAGContext(query="Who is Goku?", media_type="anime")
    assert ctx.query == "Who is Goku?"
    assert ctx.model_config.get("arbitrary_types_allowed") is True


def test_combat_character_aliasing():
    """Verify CombatCharacter correctly uses aliases and doesn't have duplicate config."""
    stats = CombatStats(tier="Low 7-C")
    char = CombatCharacter(
        Name="Tanjiro",
        Franchise="Demon Slayer",
        Stats=stats,
        Summary="Protagonist with Sun Breathing.",
    )
    assert char.name == "Tanjiro"
    assert char.franchise == "Demon Slayer"
    assert char.stats.tier == "Low 7-C"


def test_validation_error_on_invalid_types():
    """Verify Pydantic validation catches type errors."""
    with pytest.raises(ValidationError):
        # logprob must be float
        TokenLogProb(token="Test", logprob="high")
