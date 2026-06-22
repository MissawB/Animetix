"""Real-behavior tests for adapters.inference.fallback_adapter.

FallbackInferenceAdapter orchestrates an ordered list of InferencePort
adapters: it tries them in order (online ones first) and falls through to the
next when one fails, returns None / an "Erreur"-prefixed text, or raises. When
all fail, each method returns its own documented default (or raises, for
generate_structured).

These tests use REAL subclasses of InferencePort (not MagicMock) so the
adapter's capability-detection (`_is_method_overridden`, which explicitly
ignores mocks) actually registers the fakes — letting us assert the genuine
fallback ORDER: provider A fails -> B is tried -> B's result returned; all fail
-> default. No network, no real sleeps of consequence.
"""

import pytest
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.domain.entities.ai_schemas import (
    InferenceMetadata,
    InferenceResponse,
    TokenLogProb,
)
from core.ports.inference_port import InferenceNotImplementedError, InferencePort

# --- test doubles ------------------------------------------------------------


class BaseFake(InferencePort):
    """Concrete InferencePort whose abstract methods are no-ops by default.

    Being a real (non-mock) subclass means overridden methods are detected by
    the capability cache. Each test subclass overrides only what it needs.
    """

    def __init__(self, name="Fake", online=True):
        super().__init__()
        self._name = name
        self._online = online
        self.calls = []

    # Give each instance a distinct class name so logs/ordering are readable.
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def health_check(self) -> dict:
        return {"status": "online" if self._online else "offline"}

    def generate(self, prompt, system_prompt="sys", **kwargs):  # pragma: no cover
        raise NotImplementedError

    def stream_generate(self, prompt, system_prompt="sys", **kwargs):  # noqa
        raise NotImplementedError

    def get_text_embedding(self, text):  # pragma: no cover
        raise NotImplementedError


def _resp(text, usage=None, logprobs=None):
    meta = InferenceMetadata(usage=usage, logprobs=logprobs)
    return InferenceResponse(text=text, metadata=meta)


# === generate: fallback order ================================================


def test_generate_first_success_short_circuits():
    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            self.calls.append(prompt)
            return _resp("from A")

    class B(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            self.calls.append(prompt)
            return _resp("from B")

    a, b = A("A"), B("B")
    fb = FallbackInferenceAdapter([a, b])
    res = fb.generate("Q")
    assert res.text == "from A"
    # B was never consulted.
    assert a.calls == ["Q"]
    assert b.calls == []


def test_generate_falls_through_on_erreur_prefix():
    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            self.calls.append(prompt)
            return _resp("Erreur: moteur indisponible")

    class B(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            self.calls.append(prompt)
            return _resp("recovered by B")

    a, b = A("A"), B("B")
    fb = FallbackInferenceAdapter([a, b])
    res = fb.generate("Q")
    # A's "Erreur" text is treated as failure -> B used.
    assert res.text == "recovered by B"
    assert a.calls == ["Q"] and b.calls == ["Q"]


def test_generate_falls_through_on_exception():
    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            raise RuntimeError("A crashed")

    class B(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            return _resp("B ok")

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    assert fb.generate("Q").text == "B ok"


def test_generate_all_fail_returns_critical_default():
    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            raise RuntimeError("boom-A")

    class B(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            return _resp("Erreur: B down")

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    res = fb.generate("Q")
    assert res.text.startswith("Échec critique")
    # Last error recorded is from B (the final adapter tried).
    assert "B down" in res.text


def test_generate_logs_usage_on_success():
    obs = _Obs()

    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            return _resp("ok", usage={"total_tokens": 42})

    fb = FallbackInferenceAdapter([A("A")], obs_service=obs)
    fb.generate("Q")
    assert obs.inference_logs
    # tokens come from usage.total_tokens
    assert obs.inference_logs[-1]["tokens"] == 42


def test_generate_passes_include_logprobs_only_when_supported():
    captured = {}

    class WithLogprobs(BaseFake):
        def generate(
            self, prompt, system_prompt="sys", include_logprobs=False, **kwargs
        ):
            captured["include_logprobs"] = include_logprobs
            return _resp("ok")

    fb = FallbackInferenceAdapter([WithLogprobs("W")])
    fb.generate("Q", include_logprobs=True)
    assert captured["include_logprobs"] is True


class _Obs:
    """Minimal observability double recording calls."""

    def __init__(self):
        self.errors = []
        self.inference_logs = []

    def log_error(self, error_type, message):
        self.errors.append({"type": error_type, "message": message})

    def log_inference(self, model_id, latency, tokens, metadata=None):
        self.inference_logs.append(
            {"model_id": model_id, "tokens": tokens, "metadata": metadata}
        )


def test_generate_reports_failure_to_obs_service():
    obs = _Obs()

    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            raise RuntimeError("nope")

    class B(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            return _resp("ok")

    fb = FallbackInferenceAdapter([A("A"), B("B")], obs_service=obs)
    fb.generate("Q")
    # A's crash was reported as an error + a failed inference metric.
    assert any("InferenceAdapterFailure" == e["type"] for e in obs.errors)
    assert any(
        log["metadata"] and log["metadata"].get("status") == "failed"
        for log in obs.inference_logs
    )


# === _fallback_call-backed methods ===========================================


def test_fallback_call_skips_not_implemented_then_succeeds():
    class A(BaseFake):
        def get_image_embedding(self, image_data, model_id=None):
            raise InferenceNotImplementedError("A has no embeddings")

    class B(BaseFake):
        def get_image_embedding(self, image_data, model_id=None):
            return [0.1, 0.2, 0.3]

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    assert fb.get_image_embedding(b"img") == [0.1, 0.2, 0.3]


def test_fallback_call_none_result_falls_through():
    class A(BaseFake):
        def get_text_embedding(self, text):
            return None

    class B(BaseFake):
        def get_text_embedding(self, text):
            return [1.0, 2.0]

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    assert fb.get_text_embedding("hi") == [1.0, 2.0]


def test_fallback_call_all_fail_returns_method_default_empty_list():
    class A(BaseFake):
        def get_image_embedding(self, image_data, model_id=None):
            raise RuntimeError("x")

    fb = FallbackInferenceAdapter([A("A")])
    # _fallback_call returns None -> method coalesces to [].
    assert fb.get_image_embedding(b"img") == []


def test_classify_image_default_empty_dict_when_all_fail():
    class A(BaseFake):
        def classify_image(self, image_data, candidate_labels, model_id=None):
            raise RuntimeError("x")

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.classify_image(b"img", ["cat"]) == {}


def test_moderate_content_default_is_safe_when_all_fail():
    class A(BaseFake):
        def moderate_content(self, text, categories):
            raise RuntimeError("x")

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.moderate_content("text", ["nsfw"]) == {"is_safe": True}


def test_calculate_visual_similarity_casts_to_float():
    class A(BaseFake):
        def calculate_visual_similarity(self, query, item_id, media_type):
            return 1  # int -> should become float

    fb = FallbackInferenceAdapter([A("A")])
    out = fb.calculate_visual_similarity("q", "i", "anime")
    assert out == 1.0 and isinstance(out, float)


def test_calculate_visual_similarity_default_zero():
    class A(BaseFake):
        def calculate_visual_similarity(self, query, item_id, media_type):
            return None

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.calculate_visual_similarity("q", "i", "anime") == 0.0


def test_process_manga_page_passes_through_real_result():
    class A(BaseFake):
        def process_manga_page(self, image_data):
            return {"panels": [1, 2]}

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.process_manga_page(b"img") == {"panels": [1, 2]}


def test_fallback_call_logs_warning_after_recovery():
    # A returns None (failure), B succeeds: exercises the "fell back" warning path.
    class A(BaseFake):
        def detect_objects(self, image_data, candidate_queries, model_id=None):
            return None

    class B(BaseFake):
        def detect_objects(self, image_data, candidate_queries, model_id=None):
            return [{"label": "person"}]

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    assert fb.detect_objects(b"img", ["person"]) == [{"label": "person"}]


# === rerank_documents (dedicated loop) =======================================


def test_rerank_documents_empty_documents_short_circuit():
    fb = FallbackInferenceAdapter([])
    assert fb.rerank_documents("q", []) == []


def test_rerank_documents_falls_through_on_wrong_length():
    class A(BaseFake):
        def rerank_documents(self, query, documents):
            return [0.5]  # wrong length (1 vs 2) -> treated as failure

    class B(BaseFake):
        def rerank_documents(self, query, documents):
            return [0.9, 0.1]

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    assert fb.rerank_documents("q", ["d1", "d2"]) == [0.9, 0.1]


def test_rerank_documents_all_fail_returns_zeros():
    class A(BaseFake):
        def rerank_documents(self, query, documents):
            raise RuntimeError("rr down")

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.rerank_documents("q", ["d1", "d2", "d3"]) == [0.0, 0.0, 0.0]


# === generate_structured =====================================================


def test_generate_structured_first_success():
    sentinel = {"name": "Naruto"}

    class A(BaseFake):
        def generate_structured(
            self, prompt, response_model, system_prompt="sys", max_retries=3
        ):
            return sentinel

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.generate_structured("extract", dict) is sentinel


def test_generate_structured_falls_through_on_none():
    class A(BaseFake):
        def generate_structured(
            self, prompt, response_model, system_prompt="sys", max_retries=3
        ):
            return None

    class B(BaseFake):
        def generate_structured(
            self, prompt, response_model, system_prompt="sys", max_retries=3
        ):
            return {"ok": True}

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    assert fb.generate_structured("extract", dict) == {"ok": True}


def test_generate_structured_all_fail_raises():
    class A(BaseFake):
        def generate_structured(
            self, prompt, response_model, system_prompt="sys", max_retries=3
        ):
            raise RuntimeError("structured boom")

    fb = FallbackInferenceAdapter([A("A")])
    with pytest.raises(Exception, match="structured boom"):
        fb.generate_structured("extract", dict)


# === stream_generate =========================================================


def test_stream_generate_first_adapter_streams():
    class A(BaseFake):
        def stream_generate(self, prompt, system_prompt="sys", **kwargs):
            yield _resp("chunk1")
            yield _resp("chunk2")

    fb = FallbackInferenceAdapter([A("A")])
    chunks = list(fb.stream_generate("Q"))
    assert [c.text for c in chunks] == ["chunk1", "chunk2"]


def test_stream_generate_falls_through_on_erreur_first_chunk():
    class A(BaseFake):
        def stream_generate(self, prompt, system_prompt="sys", **kwargs):
            yield _resp("Erreur: A bad")

    class B(BaseFake):
        def stream_generate(self, prompt, system_prompt="sys", **kwargs):
            yield _resp("B good1")
            yield _resp("B good2")

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    chunks = list(fb.stream_generate("Q"))
    assert [c.text for c in chunks] == ["B good1", "B good2"]


def test_stream_generate_handles_empty_stream_stopiteration():
    class A(BaseFake):
        def stream_generate(self, prompt, system_prompt="sys", **kwargs):
            return
            yield  # makes this a generator that immediately stops

    class B(BaseFake):
        def stream_generate(self, prompt, system_prompt="sys", **kwargs):
            yield _resp("B saved it")

    fb = FallbackInferenceAdapter([A("A"), B("B")])
    chunks = list(fb.stream_generate("Q"))
    assert [c.text for c in chunks] == ["B saved it"]


def test_stream_generate_all_fail_yields_generate_fallback():
    # No adapter streams successfully -> final fallback calls self.generate,
    # which itself has no working adapter -> critical-failure InferenceResponse.
    class A(BaseFake):
        def stream_generate(self, prompt, system_prompt="sys", **kwargs):
            raise RuntimeError("stream boom")

        def generate(self, prompt, system_prompt="sys", **kwargs):
            raise RuntimeError("gen boom")

    fb = FallbackInferenceAdapter([A("A")])
    chunks = list(fb.stream_generate("Q"))
    assert len(chunks) == 1
    assert chunks[0].text.startswith("Échec critique")


# === calculate_uncertainty (logprob cache fast path) =========================


def test_calculate_uncertainty_uses_cached_logprobs():
    # After a successful generate with logprobs, calculate_uncertainty for the
    # SAME completion should compute entropy/perplexity/confidence locally
    # without consulting any adapter.
    logprobs = [
        TokenLogProb(token="a", logprob=-0.2),
        TokenLogProb(token="b", logprob=-0.4),
    ]

    class A(BaseFake):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            return _resp("cached answer", logprobs=logprobs)

        def calculate_uncertainty(self, prompt, completion):
            raise AssertionError("should not be called - cache path expected")

    fb = FallbackInferenceAdapter([A("A")])
    fb.generate("Q")  # primes _last_completion / _last_logprobs
    metrics = fb.calculate_uncertainty("Q", "cached answer")
    assert set(metrics) == {"entropy", "perplexity", "confidence"}
    # avg_entropy = -(-0.2 + -0.4)/2 = 0.3
    assert metrics["entropy"] == 0.3
    assert 0.0 <= metrics["confidence"] <= 1.0


def test_calculate_uncertainty_delegates_when_no_cache():
    class A(BaseFake):
        def calculate_uncertainty(self, prompt, completion):
            return {"entropy": 0.9}

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.calculate_uncertainty("p", "different completion") == {"entropy": 0.9}


# === health_check / primary adapter management ===============================


def test_health_check_online_if_any_adapter_online():
    class A(BaseFake):
        pass

    class B(BaseFake):
        pass

    a = A("A", online=False)
    b = B("B", online=True)
    fb = FallbackInferenceAdapter([a, b])
    out = fb.health_check()
    assert out["status"] == "online"
    assert len(out["adapters"]) == 2


def test_health_check_offline_if_all_offline():
    class A(BaseFake):
        pass

    fb = FallbackInferenceAdapter([A("A", online=False)])
    assert fb.health_check()["status"] == "offline"


def test_primary_adapter_property_and_set_primary():
    class A(BaseFake):
        pass

    class B(BaseFake):
        pass

    a, b = A("A"), B("B")
    fb = FallbackInferenceAdapter([a, b])
    assert fb.primary_adapter is a
    # Promote index 1 (b) to primary.
    assert fb.set_primary_adapter(1) is True
    assert fb.primary_adapter is b
    # Out-of-range index is a no-op returning False.
    assert fb.set_primary_adapter(99) is False
    assert fb.primary_adapter is b


def test_primary_adapter_none_when_empty():
    fb = FallbackInferenceAdapter([])
    assert fb.primary_adapter is None


def test_none_adapters_are_filtered_out():
    class A(BaseFake):
        pass

    a = A("A")
    fb = FallbackInferenceAdapter([None, a, None])
    assert fb.adapters == [a]


# === offline-then-online ordering ============================================


# === remaining delegated methods (happy path coverage) =======================


def test_remaining_delegated_methods_pass_through_results():
    sentinels = {
        "get_video_temporal_embeddings": [{"t": 0}],
        "localize_video_actions": [{"start": 1}],
        "transform_image_to_anime": "img.png",
        "transform_video_to_anime": "vid.mp4",
        "generate_soundscape": "snd.wav",
        "translate_manga_page": {"translated": True},
        "inpaint_text_bubbles": "out.png",
        "generate_image_description": "a desc",
        "generate_video_description": "a vid desc",
        "get_diagnostics": {"attn": [1]},
        "clone_voice": b"voice",
        "speech_to_speech": b"reply",
        "estimate_depth": b"depthmap",
        "generate_3d_scene": {"points": 1},
        "visual_rerank": [{"url": "a"}],
        "get_multimodal_late_interaction": [[0.1]],
    }

    class A(BaseFake):
        def get_video_temporal_embeddings(self, video_data):
            return sentinels["get_video_temporal_embeddings"]

        def localize_video_actions(self, video_data, action_queries):
            return sentinels["localize_video_actions"]

        def transform_image_to_anime(self, image_data, studio_style, prompt=""):
            return sentinels["transform_image_to_anime"]

        def transform_video_to_anime(self, video_data, studio_style, prompt=""):
            return sentinels["transform_video_to_anime"]

        def generate_soundscape(self, video_metadata, prompt=None):
            return sentinels["generate_soundscape"]

        def translate_manga_page(self, image_data, target_lang="Français"):
            return sentinels["translate_manga_page"]

        def inpaint_text_bubbles(self, image_data, text_placements):
            return sentinels["inpaint_text_bubbles"]

        def generate_image_description(self, image_data, prompt=""):
            return sentinels["generate_image_description"]

        def generate_video_description(self, video_data, prompt=""):
            return sentinels["generate_video_description"]

        def get_diagnostics(self, prompt, completion):
            return sentinels["get_diagnostics"]

        def clone_voice(self, text, reference_audio, language="fr"):
            return sentinels["clone_voice"]

        def speech_to_speech(self, audio_input, system_prompt=""):
            return sentinels["speech_to_speech"]

        def estimate_depth(self, image_data):
            return sentinels["estimate_depth"]

        def generate_3d_scene(self, image_data, depth_map, mode="gaussian_splatting"):
            return sentinels["generate_3d_scene"]

        def visual_rerank(self, query, image_urls, system_prompt=""):
            return sentinels["visual_rerank"]

        def get_multimodal_late_interaction(self, image_data):
            return sentinels["get_multimodal_late_interaction"]

    fb = FallbackInferenceAdapter([A("A")])

    assert (
        fb.get_video_temporal_embeddings(b"v")
        == sentinels["get_video_temporal_embeddings"]
    )
    assert (
        fb.localize_video_actions(b"v", ["run"]) == sentinels["localize_video_actions"]
    )
    assert fb.transform_image_to_anime(b"i", "ghibli") == "img.png"
    assert fb.transform_video_to_anime(b"v", "madhouse") == "vid.mp4"
    assert fb.generate_soundscape({"scene": "x"}) == "snd.wav"
    assert fb.translate_manga_page(b"i") == {"translated": True}
    assert fb.inpaint_text_bubbles(b"i", []) == "out.png"
    assert fb.generate_image_description(b"i") == "a desc"
    assert fb.generate_video_description(b"v") == "a vid desc"
    assert fb.get_diagnostics("p", "c") == {"attn": [1]}
    assert fb.clone_voice("t", b"ref") == b"voice"
    assert fb.speech_to_speech(b"aud") == b"reply"
    assert fb.estimate_depth(b"i") == b"depthmap"
    assert fb.generate_3d_scene(b"i", b"d") == {"points": 1}
    assert fb.visual_rerank("q", ["a"]) == [{"url": "a"}]
    assert fb.get_multimodal_late_interaction(b"i") == [[0.1]]


def test_remaining_delegated_methods_return_defaults_when_all_fail():
    class A(BaseFake):
        def estimate_depth(self, image_data):
            raise RuntimeError("x")

        def clone_voice(self, text, reference_audio, language="fr"):
            raise RuntimeError("x")

        def generate_3d_scene(self, image_data, depth_map, mode="gaussian_splatting"):
            raise RuntimeError("x")

        def transform_image_to_anime(self, image_data, studio_style, prompt=""):
            raise RuntimeError("x")

    fb = FallbackInferenceAdapter([A("A")])
    assert fb.estimate_depth(b"i") == b""  # bytes default
    assert fb.clone_voice("t", b"r") == b""
    assert fb.generate_3d_scene(b"i", b"d") == {}  # dict default
    assert fb.transform_image_to_anime(b"i", "s") == ""  # str default


# === generate_image: paid chain + self-hosted worker failover ================


def test_generate_image_uses_paid_chain_when_budget_ok():
    from unittest.mock import patch

    class A(BaseFake):
        def generate_image(self, prompt, style=""):
            return "paid-image.png"

    fb = FallbackInferenceAdapter([A("A")])
    with patch("django.core.cache.cache") as cache:
        cache.get.return_value = False  # budget NOT exceeded
        out = fb.generate_image("a cat", "ghibli")
    assert out == "paid-image.png"


def test_generate_image_routes_to_worker_when_budget_exceeded():
    from unittest.mock import patch

    class A(BaseFake):
        def generate_image(self, prompt, style=""):  # pragma: no cover
            raise AssertionError("paid chain must be skipped when budget exceeded")

    fb = FallbackInferenceAdapter([A("A")])

    # Cache returns True for budget flag; worker task completes immediately.
    cache_store = {"paid_api_budget_exceeded": True}

    def cache_get(key, default=None):
        if key == "paid_api_budget_exceeded":
            return True
        if key.startswith("task_result:"):
            return {"ready": True, "state": "SUCCESS", "result": "worker-image.png"}
        return cache_store.get(key, default if default is not None else 0)

    with (
        patch("django.core.cache.cache") as cache,
        patch("animetix.tasks_client.enqueue_task", return_value="task-123") as enqueue,
    ):
        cache.get.side_effect = cache_get
        out = fb.generate_image("a dog", "cel")

    assert out == "worker-image.png"
    enqueue.assert_called_once()


def test_generate_image_failover_to_worker_on_paid_failure():
    from unittest.mock import patch

    class A(BaseFake):
        def generate_image(self, prompt, style=""):
            raise RuntimeError("paid api down")

    fb = FallbackInferenceAdapter([A("A")])

    def cache_get(key, default=None):
        if key == "paid_api_budget_exceeded":
            return False  # budget ok, so it tries paid first (which raises)
        if key.startswith("task_result:"):
            return {"ready": True, "state": "SUCCESS", "result": "fallback.png"}
        return default if default is not None else 0

    with (
        patch("django.core.cache.cache") as cache,
        patch("animetix.tasks_client.enqueue_task", return_value="t-1"),
    ):
        cache.get.side_effect = cache_get
        out = fb.generate_image("x")

    assert out == "fallback.png"


def test_generate_image_worker_raises_on_task_failure():
    from unittest.mock import patch

    fb = FallbackInferenceAdapter([])  # no paid adapters -> goes straight to worker

    def cache_get(key, default=None):
        if key == "paid_api_budget_exceeded":
            return True
        if key.startswith("task_result:"):
            return {"ready": True, "state": "FAILURE", "result": {"error": "gpu oom"}}
        return default if default is not None else 0

    with (
        patch("django.core.cache.cache") as cache,
        patch("animetix.tasks_client.enqueue_task", return_value="t-2"),
    ):
        cache.get.side_effect = cache_get
        with pytest.raises(Exception, match="gpu oom"):
            fb.generate_image("x")


def test_offline_adapter_tried_after_online_one():
    order = []

    class Online(BaseFake):
        def get_text_embedding(self, text):
            order.append("online")
            return [1.0]

    class Offline(BaseFake):
        def get_text_embedding(self, text):
            order.append("offline")
            return [2.0]

    online = Online("Online", online=True)
    offline = Offline("Offline", online=False)
    # Pass offline FIRST in the list; _get_ordered_adapters must still try the
    # online one first.
    fb = FallbackInferenceAdapter([offline, online])
    assert fb.get_text_embedding("hi") == [1.0]
    assert order == ["online"]
