"""Behavior tests for the Qwen3-VL inference adapter.

The adapter talks to a Hugging Face ``InferenceClient`` (OpenAI-compatible
``chat_completion``). Every test patches ``InferenceClient`` in the module
namespace so no model loads and no network is touched; the mock client returns
deterministic chat-completion payloads. Assertions check the real parsed /
returned values, usage logging, JSON extraction, and the error fallbacks.

Complements ``tests/adapters/test_guardrail_homogeneity.py`` (which covers the
inherited ``moderate_content`` keyword fallback) without overlapping it.
"""

from unittest.mock import MagicMock, patch

import pytest
from adapters.inference.qwen3_vl_adapter import Qwen3VLAdapter
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferenceNotImplementedError

MODULE = "adapters.inference.qwen3_vl_adapter"


def _chat_response(content):
    """Build a mock object shaped like an OpenAI-compatible chat completion."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    res = MagicMock()
    res.choices = [choice]
    return res


def _make_adapter(usage_port=None, model_id="fake-qwen"):
    """Instantiate the adapter with InferenceClient patched out (no network)."""
    with patch(f"{MODULE}.InferenceClient") as mock_cls:
        adapter = Qwen3VLAdapter(model_id=model_id, usage_port=usage_port)
    # adapter.client is the instance returned by the patched class
    return adapter, mock_cls


# --- construction --------------------------------------------------------


def test_init_builds_client_and_stores_model_id(monkeypatch):
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "env-token")
    # No revision verified for a fake id -> headers stay empty (non-strict mode).
    with patch(f"{MODULE}.InferenceClient") as mock_cls:
        adapter = Qwen3VLAdapter(model_id="fake-qwen")

    assert adapter.model_id == "fake-qwen"
    # Client constructed with the model id and the env token (explicit token absent).
    _, kwargs = mock_cls.call_args
    assert kwargs["model"] == "fake-qwen"
    assert kwargs["token"] == "env-token"
    assert kwargs["headers"] == {}  # no verified revision for fake id


def test_init_prefers_explicit_token_over_env(monkeypatch):
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "env-token")
    with patch(f"{MODULE}.InferenceClient") as mock_cls:
        Qwen3VLAdapter(model_id="fake-qwen", token="explicit-token")
    _, kwargs = mock_cls.call_args
    assert kwargs["token"] == "explicit-token"


def test_init_injects_revision_header_when_verified():
    # Patch get_verified_revision in the module namespace to simulate a pinned SHA.
    with (
        patch(f"{MODULE}.get_verified_revision", return_value="abc123"),
        patch(f"{MODULE}.InferenceClient") as mock_cls,
    ):
        Qwen3VLAdapter(model_id="pinned-model")
    _, kwargs = mock_cls.call_args
    assert kwargs["headers"] == {"X-HuggingFace-Revision": "abc123"}


# --- generate ------------------------------------------------------------


def test_generate_returns_inference_response_with_text():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response("Naruto is a ninja.")

    result = adapter.generate("Who is Naruto?")

    assert isinstance(result, InferenceResponse)
    assert result.text == "Naruto is a ninja."
    # Default max_tokens (500) and the system/user messages were forwarded.
    _, kwargs = adapter.client.chat_completion.call_args
    assert kwargs["max_tokens"] == 500
    msgs = kwargs["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[1] == {"role": "user", "content": "Who is Naruto?"}


def test_generate_thinking_budget_increases_max_tokens():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response("ok")

    adapter.generate("q", thinking_budget=250)

    _, kwargs = adapter.client.chat_completion.call_args
    assert kwargs["max_tokens"] == 750  # 500 + 250


def test_generate_thinking_mode_appends_think_instruction():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response("ok")

    adapter.generate("q", system_prompt="BASE", thinking_mode=True)

    _, kwargs = adapter.client.chat_completion.call_args
    system_content = kwargs["messages"][0]["content"]
    assert system_content.startswith("BASE")
    assert "<think>" in system_content


def test_generate_logs_usage_when_usage_port_present():
    usage = MagicMock()
    adapter, _ = _make_adapter(usage_port=usage)
    adapter.client.chat_completion.return_value = _chat_response("abcdefgh")  # 8 chars

    adapter.generate("12345678", thinking_budget=10)  # 8-char prompt

    usage.log_usage.assert_called_once()
    args, kwargs = usage.log_usage.call_args
    assert args[0] == "qwen3:generate"
    assert args[1] == 2  # input_tokens = len(prompt)//4 = 8//4
    assert args[2] == 2  # output_tokens = len(content)//4 = 8//4
    assert kwargs["allocated_budget"] == 10


def test_generate_propagates_client_error():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.side_effect = TimeoutError("endpoint timeout")

    with pytest.raises(TimeoutError, match="endpoint timeout"):
        adapter.generate("q")


# --- stream_generate -----------------------------------------------------


def test_stream_generate_yields_single_inference_response():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response("streamed")

    chunks = list(adapter.stream_generate("q"))

    assert len(chunks) == 1
    assert isinstance(chunks[0], InferenceResponse)
    assert chunks[0].text == "streamed"


# --- get_text_embedding (unsupported) ------------------------------------


def test_get_text_embedding_raises_not_implemented():
    adapter, _ = _make_adapter()
    with pytest.raises(InferenceNotImplementedError):
        adapter.get_text_embedding("anything")


# --- localize_video_actions ----------------------------------------------


def test_localize_video_actions_success_per_query():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.side_effect = [
        _chat_response("punch at 0:05"),
        _chat_response("kick at 0:10"),
    ]

    out = adapter.localize_video_actions(b"\x00\x01videobytes", ["punch?", "kick?"])

    assert out == [
        {"query": "punch?", "answer": "punch at 0:05"},
        {"query": "kick?", "answer": "kick at 0:10"},
    ]
    # The video payload was base64-encoded into a data URI in the message content.
    first_call_msgs = adapter.client.chat_completion.call_args_list[0].kwargs[
        "messages"
    ]
    video_part = first_call_msgs[0]["content"][0]
    assert video_part["type"] == "video"
    assert video_part["video"].startswith("data:video/mp4;base64,")


def test_localize_video_actions_captures_error_per_query():
    adapter, _ = _make_adapter()
    # First query fails, second succeeds -> failure is captured, loop continues.
    adapter.client.chat_completion.side_effect = [
        RuntimeError("CUDA out of memory"),
        _chat_response("ok answer"),
    ]

    out = adapter.localize_video_actions(b"vid", ["q1", "q2"])

    assert out[0]["query"] == "q1"
    assert out[0]["answer"].startswith("Error: ")
    assert "CUDA out of memory" in out[0]["answer"]
    assert out[1] == {"query": "q2", "answer": "ok answer"}


# --- visual_rerank -------------------------------------------------------


def test_visual_rerank_empty_urls_returns_empty():
    adapter, _ = _make_adapter()
    assert adapter.visual_rerank("query", []) == []
    adapter.client.chat_completion.assert_not_called()


def test_visual_rerank_parses_scores_json():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response(
        'Here are the scores: {"scores": [{"index": 0, "score": 0.9}, '
        '{"index": 1, "score": 0.2}]}'
    )

    out = adapter.visual_rerank("best fight", ["url0", "url1"])

    assert out == [
        {"index": 0, "score": 0.9},
        {"index": 1, "score": 0.2},
    ]


def test_visual_rerank_resolves_index_from_url():
    adapter, _ = _make_adapter()
    # Item lacks "index" but carries the url -> index resolved via image_urls.index.
    adapter.client.chat_completion.return_value = _chat_response(
        '{"results": [{"url": "urlB", "score": 0.7}]}'
    )

    out = adapter.visual_rerank("q", ["urlA", "urlB"])

    assert out == [{"index": 1, "score": 0.7}]


def test_visual_rerank_unknown_url_falls_back_to_position():
    adapter, _ = _make_adapter()
    # url not in image_urls -> ValueError -> index falls back to enumerate position i.
    adapter.client.chat_completion.return_value = _chat_response(
        '{"scores": [{"url": "missing-url", "score": 0.4}]}'
    )

    out = adapter.visual_rerank("q", ["urlA", "urlB"])

    assert out == [{"index": 0, "score": 0.4}]


def test_visual_rerank_invalid_inner_json_uses_uniform_fallback():
    adapter, _ = _make_adapter()
    # A brace block exists (regex matches) but its content is not valid JSON ->
    # json.loads raises, caught, then uniform 1/N fallback.
    adapter.client.chat_completion.return_value = _chat_response("{not: valid, json}")

    out = adapter.visual_rerank("q", ["u0", "u1"])

    assert out == [{"index": 0, "score": 0.5}, {"index": 1, "score": 0.5}]


def test_visual_rerank_uses_mission_prompt_verbatim():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response('{"scores": []}')

    adapter.visual_rerank("MISSION: rank these", ["u0"])

    user_msg = adapter.client.chat_completion.call_args.kwargs["messages"][1]
    text_part = user_msg["content"][0]
    assert text_part["text"] == "MISSION: rank these"  # used verbatim, not templated


def test_visual_rerank_malformed_json_uses_uniform_fallback():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.return_value = _chat_response("no json here at all")

    out = adapter.visual_rerank("q", ["u0", "u1", "u2", "u3"])

    # Uniform 1/N fallback for every image.
    assert out == [{"index": i, "score": 0.25} for i in range(4)]


def test_visual_rerank_empty_scores_list_uses_uniform_fallback():
    adapter, _ = _make_adapter()
    # Valid JSON but no usable entries -> final_results empty -> uniform fallback.
    adapter.client.chat_completion.return_value = _chat_response('{"scores": []}')

    out = adapter.visual_rerank("q", ["u0", "u1"])

    assert out == [{"index": 0, "score": 0.5}, {"index": 1, "score": 0.5}]


def test_visual_rerank_client_exception_returns_zero_scores():
    adapter, _ = _make_adapter()
    adapter.client.chat_completion.side_effect = ConnectionError("endpoint down")

    out = adapter.visual_rerank("q", ["u0", "u1"])

    # Hard-failure branch returns 0.0 for each image (distinct from the 1/N branch).
    assert out == [{"index": 0, "score": 0.0}, {"index": 1, "score": 0.0}]


def test_visual_rerank_logs_usage_units():
    usage = MagicMock()
    adapter, _ = _make_adapter(usage_port=usage)
    adapter.client.chat_completion.return_value = _chat_response('{"scores": []}')

    adapter.visual_rerank("q", ["u0", "u1", "u2"])

    usage.log_usage.assert_called_once()
    args, kwargs = usage.log_usage.call_args
    assert args[0] == "qwen3:vision:rerank"
    assert args[3] == 3  # units == number of images


# --- health_check --------------------------------------------------------


def test_health_check_reports_online():
    adapter, _ = _make_adapter()
    assert adapter.health_check() == {"status": "online", "engine": "Qwen3-VL"}
