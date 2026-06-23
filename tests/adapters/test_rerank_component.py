from unittest.mock import MagicMock

from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.components.rerank_component import RerankComponent


class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(
        self, engine, input_tokens=0, output_tokens=0, units=0, allocated_budget=0
    ):
        self.calls.append({"engine": engine, "units": units})


def _ctx(generate=None):
    return InferenceComponentContext(log_usage=_Recorder(), generate=generate)


def test_empty_documents_short_circuit():
    comp = RerankComponent(_ctx())
    assert comp.rerank_documents("q", []) == []


def test_local_cross_encoder_path(monkeypatch):
    monkeypatch.delenv("COHERE_API_KEY", raising=False)
    fake_st = MagicMock()
    fake_encoder = MagicMock()
    fake_encoder.predict.return_value = [0.9, 0.1]
    fake_st.CrossEncoder.return_value = fake_encoder
    monkeypatch.setattr(
        "adapters.inference.components.rerank_component.lazy_import",
        lambda name: fake_st,
    )
    ctx = _ctx()
    comp = RerankComponent(ctx)
    assert comp.is_loaded is False
    scores = comp.rerank_documents("q", ["a", "b"])
    assert scores == [0.9, 0.1]
    assert comp.is_loaded is True
    assert ctx.log_usage.calls[-1] == {"engine": "local:rerank", "units": 2}


def test_prompt_fallback_returns_zeros_when_generate_non_string(monkeypatch):
    # Local path raises -> prompt fallback. generate returns a non-str (mirrors the
    # real adapter returning an InferenceResponse) -> re.search raises -> zeros.
    monkeypatch.delenv("COHERE_API_KEY", raising=False)

    def boom(_name):
        raise RuntimeError("no sentence_transformers")

    monkeypatch.setattr(
        "adapters.inference.components.rerank_component.lazy_import", boom
    )
    ctx = _ctx(generate=MagicMock(return_value=MagicMock()))  # non-string
    comp = RerankComponent(ctx)
    assert comp.rerank_documents("q", ["a", "b"]) == [0.0, 0.0]
