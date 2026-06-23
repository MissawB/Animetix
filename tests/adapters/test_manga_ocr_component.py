import io
from unittest.mock import MagicMock

from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.components.manga_ocr_component import MangaOcrComponent
from PIL import Image


class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(
        self, engine, input_tokens=0, output_tokens=0, units=0, allocated_budget=0
    ):
        self.calls.append(engine)


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_success_path(monkeypatch):
    rec = _Recorder()
    fake_transformers = MagicMock()
    fake_transformers.pipeline.return_value = lambda img: [{"generated_text": "hello"}]
    monkeypatch.setattr(
        "adapters.inference.components.manga_ocr_component.transformers",
        fake_transformers,
    )
    fake_torch = MagicMock()
    fake_torch.cuda.is_available.return_value = False
    monkeypatch.setattr(
        "adapters.inference.components.manga_ocr_component.torch", fake_torch
    )

    comp = MangaOcrComponent(InferenceComponentContext(log_usage=rec))
    out = comp.process_manga_page(_png_bytes())

    assert out["status"] == "success"
    assert out["text"] == "hello"
    assert out["layout"] and out["layout"][0]["text"] == "hello"[:50]
    assert any("ocr" in e for e in rec.calls)


def test_error_path_returns_error_status(monkeypatch):
    fake_transformers = MagicMock()
    fake_transformers.pipeline.side_effect = RuntimeError("no model")
    monkeypatch.setattr(
        "adapters.inference.components.manga_ocr_component.transformers",
        fake_transformers,
    )
    fake_torch = MagicMock()
    fake_torch.cuda.is_available.return_value = False
    monkeypatch.setattr(
        "adapters.inference.components.manga_ocr_component.torch", fake_torch
    )

    comp = MangaOcrComponent(InferenceComponentContext(log_usage=MagicMock()))
    out = comp.process_manga_page(_png_bytes())
    assert out["status"] == "error"
    assert out["text"] == ""
    assert "message" in out
