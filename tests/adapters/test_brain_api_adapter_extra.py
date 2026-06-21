"""Extra real-behavior tests for adapters.inference.brain_api_adapter.

Complements tests/adapters/test_brain_api_adapter_v2.py to raise coverage of
the BrainAPIAdapter. Every HTTP call is mocked at the MODULE namespace
(`safe_http_request` / `httpx`); no real network or sleeps. Assertions check
the REAL request body + headers built and the REAL parsed response — not bare
mock-call counts.
"""

import base64
from unittest.mock import MagicMock, patch

import httpx
import pytest
from adapters.inference.brain_api_adapter import BrainAPIAdapter
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferenceNotImplementedError

MODULE = "adapters.inference.brain_api_adapter.safe_http_request"


def _resp(payload, status=200):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    return r


@pytest.fixture(autouse=True)
def _clean_brain_env(monkeypatch):
    # The repo `.env` defines BRAIN_API_URL/BRAIN_API_KEY, and the adapter falls
    # back to them when api_url/api_key are None. Clear both for every test so the
    # "url/key missing" cases stay deterministic regardless of ambient env /
    # whichever earlier test loaded .env into os.environ.
    monkeypatch.delenv("BRAIN_API_URL", raising=False)
    monkeypatch.delenv("BRAIN_API_KEY", raising=False)


@pytest.fixture
def adapter():
    return BrainAPIAdapter(api_url="http://brain:5000", api_key="dev-secret-key")


@pytest.fixture
def adapter_no_key(monkeypatch):
    # Ensure no ambient BRAIN_API_KEY leaks in (the adapter falls back to the
    # env var when api_key=None), so the "empty headers" assertion is deterministic.
    monkeypatch.delenv("BRAIN_API_KEY", raising=False)
    return BrainAPIAdapter(api_url="http://brain:5000", api_key=None)


# --- generate: usage logging, payload, errors --------------------------------


def test_generate_logs_usage_and_builds_payload():
    usage_port = MagicMock()
    a = BrainAPIAdapter(api_url="http://brain:5000", api_key="k", usage_port=usage_port)
    with patch(MODULE) as req:
        req.return_value = _resp(
            {
                "text": "ok",
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
                "thinking": "reasoned",
            }
        )
        res = a.generate(
            "Q",
            system_prompt="SYS",
            thinking_budget=64,
            thinking_mode=True,
            temperature=0.3,  # extra kwarg flows into payload
        )

    # Parsed response carries text + metadata.
    assert res.text == "ok"
    assert res.metadata.thinking == "reasoned"
    assert res.metadata.usage == {"prompt_tokens": 11, "completion_tokens": 7}

    # Real request shape.
    method, url = req.call_args.args
    kwargs = req.call_args.kwargs
    assert method == "POST"
    assert url == "http://brain:5000/generate"
    assert kwargs["headers"] == {"X-API-Key": "k"}
    assert kwargs["json"] == {
        "prompt": "Q",
        "system_prompt": "SYS",
        "thinking_budget": 64,
        "thinking_mode": True,
        "include_logprobs": False,
        "temperature": 0.3,
    }

    # Usage logged with the allocated budget passed through.
    usage_port.log_usage.assert_called_once()
    log_kwargs = usage_port.log_usage.call_args
    assert log_kwargs.args[0] == "brain:api"
    assert log_kwargs.args[1] == 11  # input tokens
    assert log_kwargs.args[2] == 7  # output tokens
    assert log_kwargs.kwargs["allocated_budget"] == 64


def test_generate_raises_when_url_missing():
    a = BrainAPIAdapter(api_url=None, api_key="k")
    with pytest.raises(ValueError, match="Brain API URL not configured"):
        a.generate("Q")


def test_generate_reraises_http_error(adapter):
    with patch(MODULE, side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            adapter.generate("Q")


def test_generate_handles_missing_usage_block(adapter):
    # No "usage" key -> tokens default to 0, no KeyError.
    with patch(MODULE) as req:
        req.return_value = _resp({"text": "bare"})
        res = adapter.generate("Q")
    assert res.text == "bare"
    assert res.metadata.logprobs is None


def test_generate_without_api_key_sends_empty_headers(adapter_no_key):
    with patch(MODULE) as req:
        req.return_value = _resp({"text": "x"})
        adapter_no_key.generate("Q")
    assert req.call_args.kwargs["headers"] == {}


# --- stream_generate ---------------------------------------------------------


def test_stream_generate_raises_when_url_missing():
    a = BrainAPIAdapter(api_url=None, api_key="k")
    with pytest.raises(ValueError, match="Brain API URL not configured"):
        next(a.stream_generate("Q"))


def test_stream_generate_builds_payload_and_yields_all_chunks(adapter):
    with patch("adapters.inference.brain_api_adapter.httpx.stream") as stream:
        res = MagicMock()
        res.iter_text.return_value = ["a", "b", "c"]
        stream.return_value.__enter__.return_value = res

        chunks = list(adapter.stream_generate("Q", thinking_mode=True))

    assert [c.text for c in chunks] == ["a", "b", "c"]
    assert all(isinstance(c, InferenceResponse) for c in chunks)
    # Endpoint + payload built correctly.
    args, kwargs = stream.call_args
    assert args == ("POST", "http://brain:5000/stream_generate")
    assert kwargs["json"]["thinking_mode"] is True
    assert kwargs["headers"] == {"X-API-Key": "dev-secret-key"}
    res.raise_for_status.assert_called_once()


def test_stream_generate_reraises_http_status_error(adapter):
    with patch("adapters.inference.brain_api_adapter.httpx.stream") as stream:
        res = MagicMock()
        res.raise_for_status.side_effect = httpx.HTTPStatusError(
            "bad", request=MagicMock(), response=MagicMock()
        )
        stream.return_value.__enter__.return_value = res
        with pytest.raises(httpx.HTTPStatusError):
            list(adapter.stream_generate("Q"))


def test_stream_generate_reraises_request_error(adapter):
    with patch("adapters.inference.brain_api_adapter.httpx.stream") as stream:
        res = MagicMock()
        res.raise_for_status.side_effect = httpx.RequestError("net down")
        stream.return_value.__enter__.return_value = res
        with pytest.raises(httpx.RequestError):
            list(adapter.stream_generate("Q"))


def test_stream_generate_reraises_generic_error(adapter):
    with patch("adapters.inference.brain_api_adapter.httpx.stream") as stream:
        stream.side_effect = ValueError("weird")
        with pytest.raises(ValueError, match="weird"):
            list(adapter.stream_generate("Q"))


# --- text embedding ----------------------------------------------------------


def test_get_text_embedding_parses_and_logs():
    usage_port = MagicMock()
    a = BrainAPIAdapter(api_url="http://brain:5000", api_key="k", usage_port=usage_port)
    with patch(MODULE) as req:
        req.return_value = _resp({"embedding": [0.1, 0.2, 0.3]})
        out = a.get_text_embedding("hello")
    assert out == [0.1, 0.2, 0.3]
    method, url = req.call_args.args
    assert url == "http://brain:5000/v1/embeddings"
    assert req.call_args.kwargs["json"] == {"text": "hello"}
    usage_port.log_usage.assert_called_once_with(
        "brain:embeddings", 0, 0, 1, allocated_budget=0
    )


def test_get_text_embedding_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.get_text_embedding("hello")


# --- image generation / sprite ----------------------------------------------


def test_generate_image_returns_url(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"image_url_or_b64": "http://img/1.png"})
        out = adapter.generate_image("a cat", style="ghibli")
    assert out == "http://img/1.png"
    assert req.call_args.args[1] == "http://brain:5000/vision/generate"
    assert req.call_args.kwargs["json"] == {"prompt": "a cat", "style": "ghibli"}


def test_generate_sprite_wraps_prompt_and_delegates(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"image_url_or_b64": "sprite.png"})
        out = adapter.generate_sprite("a knight", style="cel")
    assert out == "sprite.png"
    sent_prompt = req.call_args.kwargs["json"]["prompt"]
    assert "character sprite" in sent_prompt
    assert "a knight" in sent_prompt


def test_generate_sprite_failure_raises_not_implemented(adapter):
    with patch(MODULE, side_effect=RuntimeError("down")):
        with pytest.raises(InferenceNotImplementedError) as ei:
            adapter.generate_sprite("a knight")
    assert "down" in str(ei.value)


# --- image embedding (incl. no-URL early return) -----------------------------


def test_get_image_embedding_returns_empty_without_url():
    a = BrainAPIAdapter(api_url=None, api_key="k")
    assert a.get_image_embedding(b"\x89PNG") == []


def test_get_image_embedding_encodes_and_parses(adapter):
    raw = b"\x89PNGbytes"
    with patch(MODULE) as req:
        req.return_value = _resp({"embedding": [1.0, 2.0]})
        out = adapter.get_image_embedding(raw, model_id="clip-v2")
    assert out == [1.0, 2.0]
    body = req.call_args.kwargs["json"]
    assert body["image"] == base64.b64encode(raw).decode("utf-8")
    assert body["model_id"] == "clip-v2"
    assert req.call_args.args[1] == "http://brain:5000/vision/embedding"


def test_get_image_embedding_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.get_image_embedding(b"data")


# --- vision: classify / detect ----------------------------------------------


def test_classify_image_returns_labels(adapter):
    raw = b"img"
    with patch(MODULE) as req:
        req.return_value = _resp({"labels": {"cat": 0.9, "dog": 0.1}})
        out = adapter.classify_image(raw, ["cat", "dog"], model_id="m")
    assert out == {"cat": 0.9, "dog": 0.1}
    body = req.call_args.kwargs["json"]
    assert body["candidate_labels"] == ["cat", "dog"]
    assert body["image"] == base64.b64encode(raw).decode("utf-8")
    assert req.call_args.args[1] == "http://brain:5000/vision/classify"


def test_detect_objects_returns_list(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"objects": [{"box": [0, 0, 1, 1]}]})
        out = adapter.detect_objects(b"img", ["person"])
    assert out == [{"box": [0, 0, 1, 1]}]
    assert req.call_args.args[1] == "http://brain:5000/vision/detect"


def test_classify_image_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.classify_image(b"img", ["a"])


# --- video embeddings / localization / transforms ----------------------------


def test_get_video_temporal_embeddings(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"embeddings": [{"t": 0, "v": [0.1]}]})
        out = adapter.get_video_temporal_embeddings(b"vid")
    assert out == [{"t": 0, "v": [0.1]}]
    assert req.call_args.args[1] == "http://brain:5000/video/embeddings"


def test_localize_video_actions(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"actions": [{"start": 1, "end": 2}]})
        out = adapter.localize_video_actions(b"vid", ["run"])
    assert out == [{"start": 1, "end": 2}]
    assert req.call_args.kwargs["json"]["queries"] == ["run"]


def test_transform_image_to_anime(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"image_url_or_b64": "anime.png"})
        out = adapter.transform_image_to_anime(b"img", "ghibli", prompt="p")
    assert out == "anime.png"
    body = req.call_args.kwargs["json"]
    assert body["studio_style"] == "ghibli"
    assert body["prompt"] == "p"


def test_transform_video_to_anime(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"video_url_or_b64": "anime.mp4"})
        out = adapter.transform_video_to_anime(b"vid", "madhouse")
    assert out == "anime.mp4"
    assert req.call_args.args[1] == "http://brain:5000/video/transform/anime"


def test_transform_image_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.transform_image_to_anime(b"img", "s")


# --- audio: soundscape / clone / s2s -----------------------------------------


def test_generate_soundscape(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"audio_url_or_b64": "snd.wav"})
        out = adapter.generate_soundscape({"scene": "battle"}, prompt="epic")
    assert out == "snd.wav"
    body = req.call_args.kwargs["json"]
    assert body["video_metadata"] == {"scene": "battle"}
    assert body["prompt"] == "epic"


def test_clone_voice_roundtrips_base64(adapter):
    out_bytes = b"\x00\x01audio"
    with patch(MODULE) as req:
        req.return_value = _resp(
            {"audio_b64": base64.b64encode(out_bytes).decode("utf-8")}
        )
        out = adapter.clone_voice("bonjour", b"ref-audio", language="en")
    assert out == out_bytes  # decoded back from base64
    body = req.call_args.kwargs["json"]
    assert body["language"] == "en"
    assert body["reference_audio"] == base64.b64encode(b"ref-audio").decode("utf-8")


def test_speech_to_speech_roundtrips_base64(adapter):
    out_bytes = b"reply-audio"
    with patch(MODULE) as req:
        req.return_value = _resp(
            {"audio_b64": base64.b64encode(out_bytes).decode("utf-8")}
        )
        out = adapter.speech_to_speech(b"in-audio", system_prompt="be nice")
    assert out == out_bytes
    assert req.call_args.args[1] == "http://brain:5000/audio/speech-to-speech"


def test_clone_voice_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.clone_voice("t", b"ref")


# --- depth / 3d --------------------------------------------------------------


def test_estimate_depth_decodes_b64(adapter):
    depth = b"depthmap"
    with patch(MODULE) as req:
        req.return_value = _resp({"depth_b64": base64.b64encode(depth).decode("utf-8")})
        out = adapter.estimate_depth(b"img")
    assert out == depth


def test_generate_3d_scene(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"scene_data": {"points": 1000}})
        out = adapter.generate_3d_scene(b"img", b"depth")
    assert out == {"points": 1000}
    body = req.call_args.kwargs["json"]
    assert body["image"] == base64.b64encode(b"img").decode("utf-8")
    assert body["depth_map"] == base64.b64encode(b"depth").decode("utf-8")


# --- manga -------------------------------------------------------------------


def test_process_manga_page_returns_full_json(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"panels": [], "text": "x"})
        out = adapter.process_manga_page(b"img")
    assert out == {"panels": [], "text": "x"}


def test_translate_manga_page(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"translated": True})
        out = adapter.translate_manga_page(b"img", target_lang="English")
    assert out == {"translated": True}
    assert req.call_args.kwargs["json"]["target_lang"] == "English"


def test_inpaint_text_bubbles(adapter):
    placements = [{"x": 1, "y": 2, "text": "hi"}]
    with patch(MODULE) as req:
        req.return_value = _resp({"image_url_or_b64": "out.png"})
        out = adapter.inpaint_text_bubbles(b"img", placements)
    assert out == "out.png"
    assert req.call_args.kwargs["json"]["text_placements"] == placements


def test_process_manga_page_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.process_manga_page(b"img")


# --- descriptions ------------------------------------------------------------


def test_generate_image_description(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"description": "a red sky"})
        out = adapter.generate_image_description(b"img", prompt="describe")
    assert out == "a red sky"
    assert req.call_args.kwargs["json"]["prompt"] == "describe"


def test_generate_video_description(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"description": "a fight scene"})
        out = adapter.generate_video_description(b"vid")
    assert out == "a fight scene"
    assert req.call_args.args[1] == "http://brain:5000/video/describe"


# --- rerank / diagnostics / uncertainty / visual rerank / late interaction ---


def test_rerank_documents(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"scores": [0.8, 0.2]})
        out = adapter.rerank_documents("q", ["d1", "d2"])
    assert out == [0.8, 0.2]
    body = req.call_args.kwargs["json"]
    assert body == {"query": "q", "documents": ["d1", "d2"]}
    assert req.call_args.args[1] == "http://brain:5000/v1/rerank"


def test_get_diagnostics(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"diagnostics": {"attn": [1]}})
        out = adapter.get_diagnostics("p", "c")
    assert out == {"attn": [1]}


def test_calculate_uncertainty(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"uncertainty_metrics": {"entropy": 0.4}})
        out = adapter.calculate_uncertainty("p", "c")
    assert out == {"entropy": 0.4}


def test_visual_rerank(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"reranked_items": [{"url": "a", "score": 1}]})
        out = adapter.visual_rerank("q", ["a", "b"], system_prompt="judge")
    assert out == [{"url": "a", "score": 1}]
    body = req.call_args.kwargs["json"]
    assert body["image_urls"] == ["a", "b"]
    assert body["system_prompt"] == "judge"


def test_get_multimodal_late_interaction(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
        out = adapter.get_multimodal_late_interaction(b"img")
    assert out == [[0.1, 0.2], [0.3, 0.4]]


def test_rerank_documents_reraises(adapter):
    with patch(MODULE, side_effect=RuntimeError("x")):
        with pytest.raises(RuntimeError):
            adapter.rerank_documents("q", ["d"])


# --- moderation: native path + super() fallback ------------------------------


def test_moderate_content_returns_native_payload(adapter):
    with patch(MODULE) as req:
        req.return_value = _resp({"moderation": {"is_safe": True, "score": 0.0}})
        out = adapter.moderate_content("hello", ["nsfw"])
    assert out == {"is_safe": True, "score": 0.0}
    body = req.call_args.kwargs["json"]
    assert body == {"text": "hello", "categories": ["nsfw"]}


def test_moderate_content_falls_back_to_super_on_error(adapter):
    # Native endpoint fails -> falls back to base class keyword heuristic, which
    # itself calls generate_structured -> generate. Make generate raise so the
    # keyword fallback inside the base class is exercised, with a flagged word.
    with patch(MODULE, side_effect=RuntimeError("api down")):
        with patch.object(adapter, "generate", side_effect=RuntimeError("no llm")):
            out = adapter.moderate_content("this is nsfw content", ["x"])
    assert out["is_safe"] is False
    assert "nsfw" in out["detected_categories"]
    assert out["action"] == "block"


# --- generate_structured delegates to base implementation --------------------


def test_generate_structured_delegates_to_super(adapter):
    # Base generate_structured calls self.generate; return JSON text it can parse.
    with patch.object(adapter, "generate") as gen:
        gen.return_value = InferenceResponse(text='{"name": "Naruto", "rank": 1}')
        out = adapter.generate_structured("extract", dict)
    assert out == {"name": "Naruto", "rank": 1}


def test_generate_structured_reraises_on_total_failure(adapter):
    with patch.object(adapter, "generate", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            adapter.generate_structured("extract", dict, max_retries=1)


# --- health_check: online / degraded / offline -------------------------------


def test_health_check_online(adapter):
    with patch("adapters.inference.brain_api_adapter.httpx.get") as get:
        get.return_value = MagicMock(status_code=200)
        out = adapter.health_check()
    assert out["status"] == "online"
    assert out["engine"] == "BrainAPI"
    assert "latency_ms" in out
    assert get.call_args.args[0] == "http://brain:5000/health"


def test_health_check_degraded_on_non_200(adapter):
    with patch("adapters.inference.brain_api_adapter.httpx.get") as get:
        get.return_value = MagicMock(status_code=503)
        out = adapter.health_check()
    assert out["status"] == "degraded"


def test_health_check_offline_on_exception(adapter):
    with patch(
        "adapters.inference.brain_api_adapter.httpx.get",
        side_effect=httpx.ConnectError("refused"),
    ):
        out = adapter.health_check()
    assert out == {"status": "offline", "engine": "BrainAPI"}


# --- error re-raise contract for the remaining passthrough methods -----------
# Each of these wraps safe_http_request in try/except that logs and re-raises.
# Parametrized to exercise every error branch with a single helper.


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.detect_objects(b"img", ["x"]),
        lambda a: a.get_video_temporal_embeddings(b"vid"),
        lambda a: a.localize_video_actions(b"vid", ["run"]),
        lambda a: a.transform_video_to_anime(b"vid", "s"),
        lambda a: a.generate_soundscape({"k": 1}),
        lambda a: a.speech_to_speech(b"aud"),
        lambda a: a.estimate_depth(b"img"),
        lambda a: a.generate_3d_scene(b"img", b"depth"),
        lambda a: a.translate_manga_page(b"img"),
        lambda a: a.inpaint_text_bubbles(b"img", []),
        lambda a: a.generate_image_description(b"img"),
        lambda a: a.generate_video_description(b"vid"),
        lambda a: a.get_diagnostics("p", "c"),
        lambda a: a.calculate_uncertainty("p", "c"),
        lambda a: a.visual_rerank("q", ["a"]),
        lambda a: a.get_multimodal_late_interaction(b"img"),
    ],
)
def test_passthrough_methods_reraise_on_error(adapter, call):
    with patch(MODULE, side_effect=RuntimeError("api boom")):
        with pytest.raises(RuntimeError, match="api boom"):
            call(adapter)
