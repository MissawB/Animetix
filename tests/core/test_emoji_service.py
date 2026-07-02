from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.emoji_service import EmojiDomainService


@pytest.mark.asyncio
async def test_agenerate_emojis_stream_consumes_inferenceresponse(
    emoji_service, mock_llm_service
):
    mock_llm_service.prompt_manager.get_prompt.return_value = ("p", "s")

    async def _astream(prompt, system_prompt=None):
        yield InferenceResponse(text="🍥")
        yield InferenceResponse(text="🦊")

    mock_llm_service.inference_engine.astream_generate.side_effect = _astream

    captured = {}

    def fake_parse(text):
        captured["full"] = text
        return ["🍥", "🦊"]

    emoji_service._parse_emojis = fake_parse

    with patch("asyncio.sleep", new=AsyncMock()):
        events = [
            e
            async for e in emoji_service.agenerate_emojis_stream(
                "Anime", "Naruto", "desc"
            )
        ]

    result = [e for e in events if e["type"] == "result"]
    assert result and result[0]["content"] == ["🍥", "🦊"]
    assert captured["full"] == "🍥🦊"


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def emoji_service(mock_llm_service):
    return EmojiDomainService(llm_service=mock_llm_service)


def test_generate_emojis_stream_consumes_inferenceresponse(
    emoji_service, mock_llm_service
):
    mock_llm_service.prompt_manager.get_prompt.return_value = ("p", "s")
    mock_llm_service.inference_engine.stream_generate.return_value = iter(
        [InferenceResponse(text="🍥"), InferenceResponse(text="🦊")]
    )
    # Mock the parser (it lazily imports the optional `emoji` package) so this test
    # targets the .text bug — i.e. that both chunks' .text assemble into the string
    # passed to the parser — not emoji parsing.
    captured = {}

    def fake_parse(text):
        captured["full"] = text
        return ["🍥", "🦊"]

    emoji_service._parse_emojis = fake_parse

    with patch("time.sleep"):
        events = list(emoji_service.generate_emojis_stream("Anime", "Naruto", "desc"))

    result = [e for e in events if e["type"] == "result"]
    assert result and result[0]["content"] == ["🍥", "🦊"]
    assert captured["full"] == "🍥🦊"


def test_select_secret(emoji_service):
    catalog = {"titles": ["A", "B"], "title_to_full_data": {"A": {}, "B": {}}}
    secret = emoji_service.select_secret(catalog)
    assert secret in ["A", "B"]


def test_select_secret_empty(emoji_service):
    catalog = {"titles": []}
    assert emoji_service.select_secret(catalog) is None


def test_generate_emojis(emoji_service, mock_llm_service):
    mock_llm_service.generate_emojis.return_value = "🍥🦊"
    res = emoji_service.generate_emojis("Anime", "Naruto", "Ninja story")
    assert res == "🍥🦊"
    mock_llm_service.generate_emojis.assert_called_once_with(
        "Anime", "Naruto", "Ninja story"
    )


# ── CPU sequence (no LLM) ──────────────────────────────────────────────────


def test_build_sequence_uses_precomputed(emoji_service):
    sequences = {"Anime": {"42": ["🗺️", "👻", "⚔️"]}}
    item = {"id": 42, "genres": ["Action"]}
    seq = emoji_service.build_sequence(sequences, "Anime", item)
    assert seq == ["🗺️", "👻", "⚔️"]
    # Returns a copy, not the stored list.
    seq.append("💥")
    assert sequences["Anime"]["42"] == ["🗺️", "👻", "⚔️"]


def test_build_sequence_falls_back_on_missing(emoji_service):
    # No precomputed entry for this id → lexical fallback from genres/tags.
    item = {"id": 999, "genres": ["Horror"], "tags": ["Vampire", "School"]}
    seq = emoji_service.build_sequence({"Anime": {}}, "Anime", item)
    assert "👻" in seq  # horror
    assert "🧛" in seq  # vampire
    assert "🏫" in seq  # school
    assert len(seq) == len(set(seq))  # deduped


def test_fallback_sequence_default_when_no_match(emoji_service):
    seq = emoji_service.build_sequence({}, "Anime", {"id": 1, "genres": []})
    assert seq == ["❓", "❓", "❓"]


def test_fallback_sequence_handles_stringified_lists(emoji_service):
    # Repositories sometimes store list fields as their repr string.
    item = {"id": 2, "genres": "['Comedy', 'Romance']"}
    seq = emoji_service.build_sequence({}, "Anime", item)
    assert "😂" in seq  # comedy
    assert "❤️" in seq  # romance
