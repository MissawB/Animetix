"""Real-behavior unit tests for adapters.inference.unified_inference_adapter.

The UnifiedInferenceAdapter talks to a local Ollama / OpenAI-compatible HTTP
endpoint. Every outbound call is mocked at the MODULE namespace
(`safe_http_request`, `is_safe_url`, `httpx.Client`, `time.sleep`) so there is
no real network, no ollama, and no real sleeps. Assertions check the REAL
request shape (URL / payload / headers built by the adapter) and the REAL
parsed `InferenceResponse` / dicts it returns — not bare mock-call counts.

Complements the integration-marked tests/adapters/test_unified_inference_structured.py
(which exercises generate_structured against the real generate()).
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.exceptions import InferenceError

REQ = "adapters.inference.unified_inference_adapter.safe_http_request"
SAFE_URL = "adapters.inference.unified_inference_adapter.is_safe_url"
SLEEP = "adapters.inference.unified_inference_adapter.time.sleep"


def _resp(payload, status=200):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    r.raise_for_status.return_value = None
    return r


@pytest.fixture(autouse=True)
def _clean_llm_env(monkeypatch):
    # The repo `.env` may define LLM_API_BASE / LLM_MODEL_NAME / LLM_API_KEY,
    # and the adapter falls back to them when the ctor args are None. Clear them
    # so the default-construction assertions stay deterministic regardless of
    # ambient env or whichever earlier test loaded .env into os.environ.
    monkeypatch.delenv("LLM_API_BASE", raising=False)
    monkeypatch.delenv("LLM_MODEL_NAME", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _no_real_sleep():
    # generate() sleeps 1s between RequestError retries — never wait for real.
    with patch(SLEEP):
        yield


@pytest.fixture
def adapter():
    return UnifiedInferenceAdapter(
        api_base="http://llm:8000/v1", model_name="my-model", api_key="secret"
    )


# --- construction / defaults -------------------------------------------------


def test_defaults_when_no_args_and_no_env():
    a = UnifiedInferenceAdapter()
    assert a.api_base == "http://localhost:11434/v1"
    assert a.model_name == "qwen3.5"
    assert a.api_key == "ollama"


def test_env_vars_used_when_args_missing(monkeypatch):
    monkeypatch.setenv("LLM_API_BASE", "http://env-host/v1")
    monkeypatch.setenv("LLM_MODEL_NAME", "env-model")
    monkeypatch.setenv("LLM_API_KEY", "env-key")
    a = UnifiedInferenceAdapter()
    assert a.api_base == "http://env-host/v1"
    assert a.model_name == "env-model"
    assert a.api_key == "env-key"


def test_explicit_args_take_precedence_over_env(monkeypatch):
    monkeypatch.setenv("LLM_API_BASE", "http://env-host/v1")
    a = UnifiedInferenceAdapter(api_base="http://explicit/v1", model_name="m")
    assert a.api_base == "http://explicit/v1"


def test_headers_include_bearer_when_key_present(adapter):
    assert adapter._get_headers() == {
        "Content-Type": "application/json",
        "Authorization": "Bearer secret",
    }


def test_headers_omit_auth_when_key_falsy():
    # The ctor coerces an empty key to the "ollama" default, so to hit the
    # no-Authorization branch we clear the attribute directly post-construction.
    a = UnifiedInferenceAdapter(api_base="http://x/v1", model_name="m", api_key="")
    a.api_key = ""
    assert a._get_headers() == {"Content-Type": "application/json"}


# --- get_text_embedding ------------------------------------------------------


def test_embedding_openai_data_path(adapter):
    with patch(REQ) as req:
        req.return_value = _resp({"data": [{"embedding": [0.1, 0.2, 0.3]}]})
        out = adapter.get_text_embedding("hello")
    assert out == [0.1, 0.2, 0.3]
    method, url = req.call_args.args
    assert method == "POST"
    assert url == "http://llm:8000/v1/embeddings"
    assert req.call_args.kwargs["json"] == {"model": "my-model", "input": "hello"}
    assert req.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"


def test_embedding_top_level_embedding_key(adapter):
    with patch(REQ) as req:
        req.return_value = _resp({"embedding": [1.0, 2.0]})
        out = adapter.get_text_embedding("hi")
    assert out == [1.0, 2.0]


def test_embedding_falls_back_to_direct_ollama_api(adapter):
    # First (OpenAI) call returns 200 but with no usable embedding -> adapter
    # falls through to the direct /api/embeddings endpoint.
    first = _resp({"unexpected": True})
    second = _resp({"embedding": [9.0]})
    with patch(REQ, side_effect=[first, second]) as req:
        out = adapter.get_text_embedding("hi")
    assert out == [9.0]
    # Second call hits the direct Ollama endpoint with /v1 stripped.
    second_url = req.call_args_list[1].args[1]
    assert second_url == "http://llm:8000/api/embeddings"
    assert req.call_args_list[1].kwargs["json"] == {"model": "my-model", "prompt": "hi"}


def test_embedding_wraps_errors_in_inference_error(adapter):
    with patch(REQ, side_effect=RuntimeError("boom")):
        with pytest.raises(InferenceError, match="Embedding generation failed"):
            adapter.get_text_embedding("hi")


# --- generate: happy path, payload shape, usage logging ----------------------


def test_generate_builds_payload_and_parses_response():
    usage_port = MagicMock()
    a = UnifiedInferenceAdapter(
        api_base="http://llm:8000/v1",
        model_name="my-model",
        api_key="secret",
        usage_port=usage_port,
    )
    payload_resp = {
        "choices": [{"message": {"content": "Hello world"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3},
    }
    with patch(REQ) as req:
        req.return_value = _resp(payload_resp)
        res = a.generate("Q", system_prompt="SYS")

    assert isinstance(res, InferenceResponse)
    assert res.text == "Hello world"
    assert res.metadata.usage == {"prompt_tokens": 5, "completion_tokens": 3}
    assert a._last_completion == "Hello world"

    method, url = req.call_args.args
    assert method == "POST"
    assert url == "http://llm:8000/v1/chat/completions"
    sent = req.call_args.kwargs["json"]
    assert sent["model"] == "my-model"
    assert sent["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "Q"},
    ]
    assert sent["temperature"] == 0.7  # non-json default

    usage_port.log_usage.assert_called_once()


def test_generate_json_mode_sets_response_format_and_low_temp(adapter):
    with patch(REQ) as req:
        req.return_value = _resp({"choices": [{"message": {"content": "{}"}}]})
        adapter.generate("Q", json_mode=True)
    sent = req.call_args.kwargs["json"]
    assert sent["response_format"] == {"type": "json_object"}
    assert sent["temperature"] == 0.2


def test_generate_thinking_mode_adds_extra_body(adapter):
    with patch(REQ) as req:
        req.return_value = _resp({"choices": [{"message": {"content": "ok"}}]})
        adapter.generate("Q", thinking_mode=True, thinking_budget=128)
    sent = req.call_args.kwargs["json"]
    assert sent["extra_body"] == {"thinking_budget": 128, "thinking_mode": True}


def test_generate_logprobs_request_and_parse(adapter):
    resp = {
        "choices": [
            {
                "message": {"content": "Hi"},
                "logprobs": {
                    "content": [
                        {
                            "token": "Hi",
                            "logprob": -0.5,
                            "top_logprobs": [
                                {"token": "Hi", "logprob": -0.5},
                                {"token": "Yo", "logprob": -1.2},
                            ],
                        }
                    ]
                },
            }
        ]
    }
    with patch(REQ) as req:
        req.return_value = _resp(resp)
        res = adapter.generate("Q", include_logprobs=True)
    # Request asked for logprobs.
    sent = req.call_args.kwargs["json"]
    assert sent["logprobs"] is True
    assert sent["top_logprobs"] == 5
    # Response parsed into TokenLogProb objects.
    lps = res.metadata.logprobs
    assert len(lps) == 1
    assert lps[0].token == "Hi"
    assert lps[0].logprob == -0.5
    assert lps[0].top_logprobs == [{"Hi": -0.5}, {"Yo": -1.2}]


def test_generate_strips_after_triple_dash(adapter):
    content = "Real answer\n---\nhidden reasoning"
    with patch(REQ) as req:
        req.return_value = _resp({"choices": [{"message": {"content": content}}]})
        res = adapter.generate("Q")
    assert res.text == "Real answer"


def test_generate_non_choices_response_stringified(adapter):
    with patch(REQ) as req:
        req.return_value = _resp({"weird": "shape"})
        res = adapter.generate("Q")
    assert res.text == str({"weird": "shape"})


# --- generate: 400 retry fallbacks -------------------------------------------


def test_generate_retries_without_extra_body_on_400(adapter):
    bad = _resp({}, status=400)
    good = _resp({"choices": [{"message": {"content": "ok"}}]})
    with patch(REQ, side_effect=[bad, good]) as req:
        res = adapter.generate("Q", thinking_mode=True)
    assert res.text == "ok"
    # Second attempt must NOT carry extra_body.
    second_payload = req.call_args_list[1].kwargs["json"]
    assert "extra_body" not in second_payload


def test_generate_retries_without_json_mode_on_400(adapter):
    bad = _resp({}, status=400)
    good = _resp({"choices": [{"message": {"content": "plain"}}]})
    with patch(REQ, side_effect=[bad, good]) as req:
        res = adapter.generate("Q", json_mode=True)
    assert res.text == "plain"
    second_payload = req.call_args_list[1].kwargs["json"]
    assert "response_format" not in second_payload


# --- generate: error handling ------------------------------------------------


def test_generate_retries_on_request_error_then_raises(adapter):
    with patch(REQ, side_effect=httpx.RequestError("down")) as req:
        with pytest.raises(InferenceError, match="indisponible"):
            adapter.generate("Q")
    # max_retries defaults to 3 -> three attempts.
    assert req.call_count == 3


def test_generate_breaks_immediately_on_unexpected_error(adapter):
    # A non-RequestError exception breaks the retry loop after one attempt.
    with patch(REQ, side_effect=ValueError("weird")) as req:
        with pytest.raises(InferenceError):
            adapter.generate("Q")
    assert req.call_count == 1


def test_generate_raises_inference_error_on_http_status(adapter):
    bad = _resp({}, status=500)
    bad.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500", request=MagicMock(), response=MagicMock()
    )
    with patch(REQ, return_value=bad):
        with pytest.raises(InferenceError):
            adapter.generate("Q")


# --- stream_generate ---------------------------------------------------------


def _stream_client(lines, status=200):
    """Build a fake httpx.Client context whose stream yields SSE `lines`."""
    res = MagicMock()
    res.status_code = status
    res.raise_for_status.return_value = None
    res.iter_lines.return_value = lines

    stream_cm = MagicMock()
    stream_cm.__enter__.return_value = res
    stream_cm.__exit__.return_value = False

    client = MagicMock()
    client.stream.return_value = stream_cm

    client_cm = MagicMock()
    client_cm.__enter__.return_value = client
    client_cm.__exit__.return_value = False
    return client_cm, res, client


def test_stream_generate_yields_content_deltas(adapter):
    lines = [
        "data: " + json.dumps({"choices": [{"delta": {"content": "Hel"}}]}),
        "data: " + json.dumps({"choices": [{"delta": {"content": "lo"}}]}),
        "data: [DONE]",
    ]
    client_cm, res, client = _stream_client(lines)
    with (
        patch(SAFE_URL, return_value=True),
        patch(
            "adapters.inference.unified_inference_adapter.httpx.Client",
            return_value=client_cm,
        ),
    ):
        chunks = list(adapter.stream_generate("Q", system_prompt="SYS"))

    assert [c.text for c in chunks] == ["Hel", "lo"]
    assert all(isinstance(c, InferenceResponse) for c in chunks)
    assert adapter._last_completion == "Hello"
    # Stream payload carries stream=True and proper messages.
    sent = client.stream.call_args.kwargs["json"]
    assert sent["stream"] is True
    assert sent["messages"][0] == {"role": "system", "content": "SYS"}


def test_stream_generate_skips_unparseable_chunks(adapter):
    lines = [
        "data: not-json",
        "data: " + json.dumps({"choices": [{"delta": {"content": "ok"}}]}),
        "data: [DONE]",
    ]
    client_cm, res, client = _stream_client(lines)
    with (
        patch(SAFE_URL, return_value=True),
        patch(
            "adapters.inference.unified_inference_adapter.httpx.Client",
            return_value=client_cm,
        ),
    ):
        chunks = list(adapter.stream_generate("Q"))
    # Bad chunk skipped, good one yielded.
    assert [c.text for c in chunks] == ["ok"]


def test_stream_generate_rejects_unsafe_url(adapter):
    with patch(SAFE_URL, return_value=False):
        with pytest.raises(InferenceError, match="Streaming failed"):
            list(adapter.stream_generate("Q"))


def test_stream_generate_wraps_http_status_error(adapter):
    lines = []
    client_cm, res, client = _stream_client(lines)
    res.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad", request=MagicMock(), response=MagicMock()
    )
    with (
        patch(SAFE_URL, return_value=True),
        patch(
            "adapters.inference.unified_inference_adapter.httpx.Client",
            return_value=client_cm,
        ),
    ):
        with pytest.raises(InferenceError, match="Streaming failed"):
            list(adapter.stream_generate("Q"))


# --- health_check ------------------------------------------------------------


def test_health_check_online_via_ollama_tags(adapter):
    with patch(REQ) as req:
        req.return_value = _resp({"models": [{"name": "qwen"}]})
        out = adapter.health_check()
    assert out["status"] == "online"
    assert out["engine"] == "Ollama/Unified"
    assert out["models"] == [{"name": "qwen"}]
    # First probe hits the /api/tags endpoint with /v1 stripped.
    assert req.call_args.args[1] == "http://llm:8000/api/tags"


def test_health_check_falls_back_to_openai_models(adapter):
    # Ollama probe raises -> OpenAI-compatible /models probe returns 200.
    ollama_fail = RuntimeError("no ollama")
    openai_ok = _resp({}, status=200)
    with patch(REQ, side_effect=[ollama_fail, openai_ok]):
        out = adapter.health_check()
    assert out == {"status": "online", "engine": "OpenAI-Compatible/Unified"}


def test_health_check_offline_when_both_fail(adapter):
    with patch(REQ, side_effect=RuntimeError("down")):
        out = adapter.health_check()
    assert out == {"status": "offline", "engine": "Unified"}


# --- set_model_name ----------------------------------------------------------


def test_set_model_name_updates_field(adapter):
    adapter.set_model_name("new-model")
    assert adapter.model_name == "new-model"


# --- calculate_uncertainty ---------------------------------------------------


def test_uncertainty_uses_cached_logprobs(adapter):
    from core.domain.entities.ai_schemas import TokenLogProb

    adapter._last_completion = "cached answer"
    adapter._last_logprobs = [
        TokenLogProb(token="a", logprob=-0.1),
        TokenLogProb(token="b", logprob=-0.3),
    ]
    out = adapter.calculate_uncertainty("p", "cached answer")
    # avg_neg_logprob = -((-0.1) + (-0.3))/2 = 0.2
    assert out["entropy"] == 0.2
    assert 0.0 <= out["confidence"] <= 1.0
    assert out["perplexity"] > 1.0


def test_uncertainty_heuristic_when_no_cache(adapter):
    out = adapter.calculate_uncertainty("p", "some completely fresh text here")
    assert set(out) == {"entropy", "perplexity", "confidence"}
    assert 0.0 <= out["confidence"] <= 1.0


def test_uncertainty_empty_completion_safe(adapter):
    out = adapter.calculate_uncertainty("p", "")
    assert 0.0 <= out["confidence"] <= 1.0


# --- get_diagnostics ---------------------------------------------------------


def test_diagnostics_shape(adapter):
    out = adapter.get_diagnostics("prompt", "one two three four")
    # Square attention map sized to token count (capped at 10).
    amap = out["attention_map"]
    assert len(amap) == 4
    assert all(len(row) == 4 for row in amap)
    # 3-layer logit-lens trajectory.
    assert len(out["logit_lens_trajectory"]) == 3
    assert out["model_signature"] == "my-model:native-logprobs"


def test_diagnostics_empty_completion_safe(adapter):
    out = adapter.get_diagnostics("p", "")
    assert len(out["attention_map"]) == 1
    assert len(out["logit_lens_trajectory"]) == 3


# --- generate_sprite delegates to ImageGenMixin.generate_image ---------------


def test_generate_sprite_wraps_prompt_and_delegates(adapter):
    with patch.object(adapter, "generate_image", return_value="sprite.png") as gi:
        out = adapter.generate_sprite("a knight", style="cel")
    assert out == "sprite.png"
    sent_prompt = gi.call_args.args[0]
    assert "a knight" in sent_prompt
    assert "character sheet" in sent_prompt
    assert "transparent background" in sent_prompt
    assert gi.call_args.args[1] == "cel"
