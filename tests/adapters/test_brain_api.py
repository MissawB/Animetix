"""Real-behavior tests for adapters.inference.brain_api.

NOTE: this module is the FastAPI *server* (the "Brain API"), NOT the HTTP
client `brain_api_adapter`. It defines a `FastAPI` app whose endpoints delegate
to a module-level `brain_engine` (a UnifiedInferenceAdapter). At import time it
reads BRAIN_API_KEY and calls sys.exit(1) if missing / equal to the insecure
dev key, so BRAIN_API_KEY must be set to a *non-dev* value before import.

Strategy: drive the app through FastAPI's TestClient. Authentication is bypassed
per-test via app.dependency_overrides[verify_api_key]; every endpoint delegates
to brain_engine, which we monkeypatch to return deterministic values. We assert
the REAL parsed JSON the endpoint builds (base64 round-trips, key names, nesting)
and the REAL 500 error branch (every handler wraps the call in try/except ->
HTTPException(500)). No network, no real inference.
"""

import base64
import os

import pytest
from fastapi.testclient import TestClient

# The module exits at import if BRAIN_API_KEY is missing or the insecure dev key.
# setdefault avoids clobbering a real key from the environment / CI secrets.
os.environ.setdefault("BRAIN_API_KEY", "secure-test-key-brain-api")

from adapters.inference.brain_api import (  # noqa: E402
    EXPECTED_API_KEY,
    app,
    brain_engine,
    verify_api_key,
)

VALID_KEY = os.environ["BRAIN_API_KEY"]


@pytest.fixture
def client():
    """TestClient with auth dependency overridden (so handlers actually run)."""
    app.dependency_overrides[verify_api_key] = lambda: VALID_KEY
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture
def raw_client():
    """TestClient WITHOUT the auth override, to exercise the real auth path."""
    app.dependency_overrides.clear()
    return TestClient(app)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


# --- import-time invariant ---------------------------------------------------


def test_expected_api_key_loaded_from_env():
    # Module captured the env var at import; if it had been missing the module
    # would have called sys.exit(1) and import would have failed.
    assert EXPECTED_API_KEY == VALID_KEY


# --- authentication ----------------------------------------------------------


def test_generate_requires_api_key(raw_client):
    # No X-API-Key header -> verify_api_key raises 401.
    resp = raw_client.post("/generate", json={"prompt": "hi"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or missing API Key"


def test_generate_wrong_api_key_rejected(raw_client):
    resp = raw_client.post(
        "/generate", json={"prompt": "hi"}, headers={"X-API-Key": "nope"}
    )
    assert resp.status_code == 401


def test_generate_correct_api_key_accepted(raw_client, monkeypatch):
    class _Res:
        text = "ok"
        metadata = None

    monkeypatch.setattr(brain_engine, "generate", lambda *a, **k: _Res())
    resp = raw_client.post(
        "/generate", json={"prompt": "hi"}, headers={"X-API-Key": VALID_KEY}
    )
    assert resp.status_code == 200


# --- health (no auth) --------------------------------------------------------


def test_health_delegates_to_engine(monkeypatch):
    monkeypatch.setattr(
        brain_engine, "health_check", lambda: {"status": "online", "engine": "Unified"}
    )
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "online", "engine": "Unified"}


# --- generate: response shaping ----------------------------------------------


def test_generate_serializes_text_usage_and_logprobs(client, monkeypatch):
    class _LP:
        token = "Na"
        logprob = -0.5
        top_logprobs = [{"Na": -0.5}]

    class _Meta:
        usage = {"prompt_tokens": 3, "completion_tokens": 5}
        logprobs = [_LP()]

    class _Res:
        text = "Naruto"
        metadata = _Meta()

    captured = {}

    def fake_generate(prompt, system_prompt, **kwargs):
        captured["prompt"] = prompt
        captured["system_prompt"] = system_prompt
        captured["kwargs"] = kwargs
        return _Res()

    monkeypatch.setattr(brain_engine, "generate", fake_generate)
    resp = client.post(
        "/generate",
        json={
            "prompt": "Who is the MC?",
            "system_prompt": "SYS",
            "thinking_budget": 32,
            "thinking_mode": True,
            "include_logprobs": True,
        },
        headers={"X-API-Key": VALID_KEY},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["text"] == "Naruto"
    assert body["usage"] == {"prompt_tokens": 3, "completion_tokens": 5}
    assert body["logprobs"] == [
        {"token": "Na", "logprob": -0.5, "top_logprobs": [{"Na": -0.5}]}
    ]
    # The engine received the request fields it should.
    assert captured["prompt"] == "Who is the MC?"
    assert captured["system_prompt"] == "SYS"
    assert captured["kwargs"]["thinking_budget"] == 32
    assert captured["kwargs"]["thinking_mode"] is True
    assert captured["kwargs"]["include_logprobs"] is True


def test_generate_without_metadata_yields_empty_usage_null_logprobs(
    client, monkeypatch
):
    class _Res:
        text = "bare"
        metadata = None

    monkeypatch.setattr(brain_engine, "generate", lambda *a, **k: _Res())
    resp = client.post("/generate", json={"prompt": "x"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["usage"] == {}
    assert body["logprobs"] is None


def test_generate_error_branch_returns_500(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("engine down")

    monkeypatch.setattr(brain_engine, "generate", boom)
    resp = client.post("/generate", json={"prompt": "x"})
    assert resp.status_code == 500
    assert resp.json()["detail"] == "engine down"


# --- similarity --------------------------------------------------------------


def test_visual_similarity_returns_score(client, monkeypatch):
    captured = {}

    def fake(query, item_id, media_type):
        captured.update(query=query, item_id=item_id, media_type=media_type)
        return 0.87

    monkeypatch.setattr(brain_engine, "calculate_visual_similarity", fake)
    resp = client.post(
        "/similarity/visual",
        json={"query": "naruto vibe", "item_id": "a1", "media_type": "anime"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"score": 0.87}
    assert captured == {
        "query": "naruto vibe",
        "item_id": "a1",
        "media_type": "anime",
    }


def test_visual_similarity_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "calculate_visual_similarity",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("bad")),
    )
    resp = client.post(
        "/similarity/visual",
        json={"query": "q", "item_id": "i", "media_type": "m"},
    )
    assert resp.status_code == 500
    assert resp.json()["detail"] == "bad"


# --- vision: embedding / detect / describe -----------------------------------


def test_vision_embedding_decodes_base64_and_returns_embedding(client, monkeypatch):
    raw = b"\x89PNG-bytes"
    seen = {}

    def fake(img_bytes, model_id):
        seen["img"] = img_bytes
        seen["model_id"] = model_id
        return [0.1, 0.2]

    monkeypatch.setattr(brain_engine, "get_image_embedding", fake)
    resp = client.post(
        "/vision/embedding", json={"image": _b64(raw), "model_id": "clip"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"embedding": [0.1, 0.2]}
    # The endpoint base64-decoded the image before delegating.
    assert seen["img"] == raw
    assert seen["model_id"] == "clip"


def test_vision_embedding_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "get_image_embedding",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("emb fail")),
    )
    resp = client.post("/vision/embedding", json={"image": _b64(b"x")})
    assert resp.status_code == 500
    assert resp.json()["detail"] == "emb fail"


def test_vision_detect_returns_objects(client, monkeypatch):
    seen = {}

    def fake(img, labels, model_id):
        seen.update(img=img, labels=labels, model_id=model_id)
        return [{"label": "person", "box": [0, 0, 1, 1]}]

    monkeypatch.setattr(brain_engine, "detect_objects", fake)
    resp = client.post(
        "/vision/detect",
        json={"image": _b64(b"img"), "candidate_labels": ["person", "dog"]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"objects": [{"label": "person", "box": [0, 0, 1, 1]}]}
    assert seen["labels"] == ["person", "dog"]
    assert seen["img"] == b"img"


def test_vision_describe_returns_description(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "generate_image_description",
        lambda img, prompt: f"desc:{prompt}",
    )
    resp = client.post("/vision/describe", json={"image": _b64(b"img"), "prompt": "go"})
    assert resp.status_code == 200
    assert resp.json() == {"description": "desc:go"}


def test_vision_describe_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "generate_image_description",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("vlm down")),
    )
    resp = client.post("/vision/describe", json={"image": _b64(b"img")})
    assert resp.status_code == 500


# --- video describe / embeddings / localize ----------------------------------


def test_video_describe(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine, "generate_video_description", lambda vid, prompt: "a fight"
    )
    resp = client.post("/video/describe", json={"video": _b64(b"vid")})
    assert resp.status_code == 200
    assert resp.json() == {"description": "a fight"}


def test_video_embeddings(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "get_video_temporal_embeddings",
        lambda vid: [{"t": 0, "v": [0.1]}],
    )
    resp = client.post("/video/embeddings", json={"video": _b64(b"vid")})
    assert resp.status_code == 200
    assert resp.json() == {"embeddings": [{"t": 0, "v": [0.1]}]}


def test_video_localize(client, monkeypatch):
    seen = {}

    def fake(vid, queries):
        seen["queries"] = queries
        return [{"start": 1, "end": 2}]

    monkeypatch.setattr(brain_engine, "localize_video_actions", fake)
    resp = client.post(
        "/video/localize", json={"video": _b64(b"vid"), "queries": ["run"]}
    )
    assert resp.status_code == 200
    assert resp.json() == {"actions": [{"start": 1, "end": 2}]}
    assert seen["queries"] == ["run"]


def test_video_localize_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "localize_video_actions",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("loc fail")),
    )
    resp = client.post(
        "/video/localize", json={"video": _b64(b"vid"), "queries": ["x"]}
    )
    assert resp.status_code == 500


# --- rerank: documents / vision ----------------------------------------------


def test_rerank_documents(client, monkeypatch):
    seen = {}

    def fake(query, documents):
        seen.update(query=query, documents=documents)
        return [0.9, 0.1]

    monkeypatch.setattr(brain_engine, "rerank_documents", fake)
    resp = client.post("/v1/rerank", json={"query": "q", "documents": ["d1", "d2"]})
    assert resp.status_code == 200
    assert resp.json() == {"scores": [0.9, 0.1]}
    assert seen == {"query": "q", "documents": ["d1", "d2"]}


def test_vision_rerank(client, monkeypatch):
    seen = {}

    def fake(query, urls, system_prompt):
        seen.update(query=query, urls=urls, system_prompt=system_prompt)
        return [{"url": "a", "score": 1.0}]

    monkeypatch.setattr(brain_engine, "visual_rerank", fake)
    resp = client.post(
        "/vision/rerank",
        json={"query": "q", "image_urls": ["a", "b"], "system_prompt": "judge"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"reranked_items": [{"url": "a", "score": 1.0}]}
    assert seen["urls"] == ["a", "b"]
    assert seen["system_prompt"] == "judge"


def test_rerank_documents_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "rerank_documents",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("rr fail")),
    )
    resp = client.post("/v1/rerank", json={"query": "q", "documents": ["d"]})
    assert resp.status_code == 500


# --- vision: depth (base64 round-trip) / classify ----------------------------


def test_vision_depth_roundtrips_base64(client, monkeypatch):
    depth_bytes = b"\x00\x01depthmap"
    monkeypatch.setattr(brain_engine, "estimate_depth", lambda img: depth_bytes)
    resp = client.post("/vision/depth", json={"image": _b64(b"img")})
    assert resp.status_code == 200
    # Endpoint re-encodes the depth bytes to base64.
    assert resp.json() == {"depth_b64": _b64(depth_bytes)}
    assert base64.b64decode(resp.json()["depth_b64"]) == depth_bytes


def test_vision_classify(client, monkeypatch):
    seen = {}

    def fake(img, labels, model_id):
        seen.update(labels=labels, model_id=model_id)
        return {"cat": 0.8, "dog": 0.2}

    monkeypatch.setattr(brain_engine, "classify_image", fake)
    resp = client.post(
        "/vision/classify",
        json={"image": _b64(b"img"), "candidate_labels": ["cat", "dog"]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"labels": {"cat": 0.8, "dog": 0.2}}
    assert seen["labels"] == ["cat", "dog"]


def test_vision_classify_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "classify_image",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("cls fail")),
    )
    resp = client.post(
        "/vision/classify",
        json={"image": _b64(b"img"), "candidate_labels": ["x"]},
    )
    assert resp.status_code == 500


# --- transforms: image / video anime -----------------------------------------


def test_transform_image_anime(client, monkeypatch):
    seen = {}

    def fake(img, style, prompt):
        seen.update(style=style, prompt=prompt)
        return "anime.png"

    monkeypatch.setattr(brain_engine, "transform_image_to_anime", fake)
    resp = client.post(
        "/vision/transform/anime",
        json={"image": _b64(b"img"), "studio_style": "ghibli", "prompt": "p"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"image_url_or_b64": "anime.png"}
    assert seen == {"style": "ghibli", "prompt": "p"}


def test_transform_video_anime(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "transform_video_to_anime",
        lambda vid, style, prompt: "anime.mp4",
    )
    resp = client.post(
        "/video/transform/anime",
        json={"video": _b64(b"vid"), "studio_style": "madhouse"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"video_url_or_b64": "anime.mp4"}


def test_transform_image_anime_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "transform_image_to_anime",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("tf fail")),
    )
    resp = client.post(
        "/vision/transform/anime",
        json={"image": _b64(b"img"), "studio_style": "s"},
    )
    assert resp.status_code == 500


# --- audio: soundscape / clone / s2s -----------------------------------------


def test_generate_soundscape(client, monkeypatch):
    seen = {}

    def fake(metadata, prompt):
        seen.update(metadata=metadata, prompt=prompt)
        return "snd.wav"

    monkeypatch.setattr(brain_engine, "generate_soundscape", fake)
    resp = client.post(
        "/audio/generate/soundscape",
        json={"video_metadata": {"scene": "battle"}, "prompt": "epic"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"audio_url_or_b64": "snd.wav"}
    assert seen["metadata"] == {"scene": "battle"}
    assert seen["prompt"] == "epic"


def test_clone_voice_roundtrips_base64(client, monkeypatch):
    out_audio = b"\x00\x01synth"
    seen = {}

    def fake(text, ref_bytes, language):
        seen.update(text=text, ref=ref_bytes, language=language)
        return out_audio

    monkeypatch.setattr(brain_engine, "clone_voice", fake)
    resp = client.post(
        "/audio/clone-voice",
        json={
            "text": "bonjour",
            "reference_audio": _b64(b"ref-audio"),
            "language": "en",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"audio_b64": _b64(out_audio)}
    # Reference audio was base64-decoded before delegating.
    assert seen["ref"] == b"ref-audio"
    assert seen["language"] == "en"


def test_speech_to_speech_roundtrips_base64(client, monkeypatch):
    out_audio = b"reply-audio"
    monkeypatch.setattr(
        brain_engine, "speech_to_speech", lambda aud, system_prompt: out_audio
    )
    resp = client.post(
        "/audio/speech-to-speech",
        json={"audio": _b64(b"in-audio"), "system_prompt": "be nice"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"audio_b64": _b64(out_audio)}


def test_clone_voice_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "clone_voice",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("voice fail")),
    )
    resp = client.post(
        "/audio/clone-voice",
        json={"text": "t", "reference_audio": _b64(b"ref")},
    )
    assert resp.status_code == 500


# --- manga: process / translate / inpaint ------------------------------------


def test_process_manga_page_returns_full_json(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "process_manga_page",
        lambda img: {"panels": [{"id": 1}], "text": "x"},
    )
    resp = client.post("/vision/manga/process", json={"image": _b64(b"img")})
    assert resp.status_code == 200
    # Endpoint returns the engine result verbatim (no wrapping key).
    assert resp.json() == {"panels": [{"id": 1}], "text": "x"}


def test_translate_manga_page(client, monkeypatch):
    seen = {}

    def fake(img, target_lang):
        seen["target_lang"] = target_lang
        return {"translated": True}

    monkeypatch.setattr(brain_engine, "translate_manga_page", fake)
    resp = client.post(
        "/vision/manga/translate",
        json={"image": _b64(b"img"), "target_lang": "English"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"translated": True}
    assert seen["target_lang"] == "English"


def test_inpaint_manga_page(client, monkeypatch):
    placements = [{"x": 1, "y": 2, "text": "hi"}]
    seen = {}

    def fake(img, text_placements):
        seen["placements"] = text_placements
        return "out.png"

    monkeypatch.setattr(brain_engine, "inpaint_text_bubbles", fake)
    resp = client.post(
        "/vision/manga/inpaint",
        json={"image": _b64(b"img"), "text_placements": placements},
    )
    assert resp.status_code == 200
    assert resp.json() == {"image_url_or_b64": "out.png"}
    assert seen["placements"] == placements


def test_process_manga_page_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "process_manga_page",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("manga fail")),
    )
    resp = client.post("/vision/manga/process", json={"image": _b64(b"img")})
    assert resp.status_code == 500


# --- diagnostics / uncertainty -----------------------------------------------


def test_diagnostics(client, monkeypatch):
    seen = {}

    def fake(prompt, completion):
        seen.update(prompt=prompt, completion=completion)
        return {"attn": [[1.0]]}

    monkeypatch.setattr(brain_engine, "get_diagnostics", fake)
    resp = client.post("/diagnostics", json={"prompt": "p", "completion": "c"})
    assert resp.status_code == 200
    assert resp.json() == {"diagnostics": {"attn": [[1.0]]}}
    assert seen == {"prompt": "p", "completion": "c"}


def test_uncertainty(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "calculate_uncertainty",
        lambda prompt, completion: {"entropy": 0.4, "perplexity": 1.2},
    )
    resp = client.post("/uncertainty", json={"prompt": "p", "completion": "c"})
    assert resp.status_code == 200
    assert resp.json() == {"uncertainty_metrics": {"entropy": 0.4, "perplexity": 1.2}}


def test_uncertainty_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "calculate_uncertainty",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("unc fail")),
    )
    resp = client.post("/uncertainty", json={"prompt": "p", "completion": "c"})
    assert resp.status_code == 500


# --- 3d / moderation / late-interaction / generate ---------------------------


def test_generate_3d_decodes_both_base64(client, monkeypatch):
    seen = {}

    def fake(img_bytes, depth_bytes):
        seen.update(img=img_bytes, depth=depth_bytes)
        return {"points": 1000}

    monkeypatch.setattr(brain_engine, "generate_3d_scene", fake)
    resp = client.post(
        "/vision/generate-3d",
        json={"image": _b64(b"img"), "depth_map": _b64(b"depth")},
    )
    assert resp.status_code == 200
    assert resp.json() == {"scene_data": {"points": 1000}}
    # Both inputs were base64-decoded before delegating.
    assert seen["img"] == b"img"
    assert seen["depth"] == b"depth"


def test_moderate(client, monkeypatch):
    seen = {}

    def fake(text, categories):
        seen.update(text=text, categories=categories)
        return {"is_safe": False, "detected_categories": ["nsfw"]}

    monkeypatch.setattr(brain_engine, "moderate_content", fake)
    resp = client.post("/moderate", json={"text": "bad", "categories": ["nsfw"]})
    assert resp.status_code == 200
    assert resp.json() == {
        "moderation": {"is_safe": False, "detected_categories": ["nsfw"]}
    }
    assert seen == {"text": "bad", "categories": ["nsfw"]}


def test_vision_late_interaction(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "get_multimodal_late_interaction",
        lambda img: [[0.1, 0.2], [0.3, 0.4]],
    )
    resp = client.post("/vision/late-interaction", json={"image": _b64(b"img")})
    assert resp.status_code == 200
    assert resp.json() == {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}


def test_vision_generate_image(client, monkeypatch):
    seen = {}

    def fake(prompt, style):
        seen.update(prompt=prompt, style=style)
        return "http://img/1.png"

    monkeypatch.setattr(brain_engine, "generate_image", fake)
    resp = client.post("/vision/generate", json={"prompt": "a cat", "style": "ghibli"})
    assert resp.status_code == 200
    assert resp.json() == {"image_url_or_b64": "http://img/1.png"}
    assert seen == {"prompt": "a cat", "style": "ghibli"}


def test_generate_3d_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "generate_3d_scene",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("3d fail")),
    )
    resp = client.post(
        "/vision/generate-3d",
        json={"image": _b64(b"img"), "depth_map": _b64(b"depth")},
    )
    assert resp.status_code == 500


def test_moderate_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "moderate_content",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mod fail")),
    )
    resp = client.post("/moderate", json={"text": "t", "categories": ["x"]})
    assert resp.status_code == 500


def test_vision_generate_image_error_branch(client, monkeypatch):
    monkeypatch.setattr(
        brain_engine,
        "generate_image",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("gen fail")),
    )
    resp = client.post("/vision/generate", json={"prompt": "x"})
    assert resp.status_code == 500
