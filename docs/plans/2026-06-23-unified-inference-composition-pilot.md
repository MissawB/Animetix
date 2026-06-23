# UnifiedInferenceAdapter mixins→composition (pilot) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert two of `UnifiedInferenceAdapter`'s eight mixins (`MangaOcrMixin`, `RerankMixin`) to composed component classes used only by that adapter, establishing a behavior-preserving composition template.

**Architecture:** New `components/` package holds a tiny shared `InferenceComponentContext` (carrying `log_usage` + `generate`) and two component classes that own their lazy model caches. `UnifiedInferenceAdapter` drops the two mixins, builds the components in `__init__`, and exposes thin delegating methods (required because the fallback's capability detection inspects the class). The mixin files and every other adapter are left untouched (transitional duplication, deduped in a follow-up).

**Tech Stack:** Python 3.12, pytest, `core.utils.lazy_import.lazy_import`, `core.utils.security.safe_http_request`.

## Global Constraints

- Behavior-preserving: no functional change to `UnifiedInferenceAdapter`'s observable behavior or public interface.
- The pilot mixins (`manga_ocr.py`, `rerank_mixin.py`) and ALL other adapters/tests stay untouched.
- Component logic is copied verbatim from the mixins (only `self._log_usage`→`ctx.log_usage`, `self.generate`→`ctx.generate`, and the lazy cache moved onto the component).
- The pre-existing rerank prompt-fallback bug (`generate` returns `InferenceResponse`, used as `str`) is preserved, not fixed.
- All tests mock LLM/GPU/HTTP — CI-safe (no live model, no network).
- Spec: `docs/specs/2026-06-23-unified-inference-composition-pilot-design.md`.

---

### Task 1: Shared context + RerankComponent

**Files:**
- Create: `backend/adapters/inference/components/__init__.py` (empty)
- Create: `backend/adapters/inference/components/context.py`
- Create: `backend/adapters/inference/components/rerank_component.py`
- Test: `tests/adapters/test_rerank_component.py`

**Interfaces:**
- Produces: `InferenceComponentContext(log_usage: Callable, generate: Optional[Callable] = None)` (a dataclass); `RerankComponent(ctx, reranker_model_name="cross-encoder/ms-marco-MiniLM-L-12-v2")` with `rerank_documents(query: str, documents: list[str]) -> list[float]` and a read-only `is_loaded: bool` property.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_rerank_component.py
from unittest.mock import MagicMock

from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.components.rerank_component import RerankComponent


class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, engine, input_tokens=0, output_tokens=0, units=0, allocated_budget=0):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/test_rerank_component.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.inference.components'`.

- [ ] **Step 3: Write the implementation**

Create `backend/adapters/inference/components/__init__.py` empty.

Create `backend/adapters/inference/components/context.py`:

```python
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class InferenceComponentContext:
    """Cross-cutting collaborators a composed inference component needs.

    Built by the host adapter from its own ``_log_usage`` and ``generate``.
    """

    log_usage: Callable[..., None]
    generate: Optional[Callable[..., Any]] = None
```

Create `backend/adapters/inference/components/rerank_component.py`:

```python
import json
import logging
import os
import re
from typing import List

from adapters.inference.components.context import InferenceComponentContext
from core.utils.lazy_import import lazy_import
from core.utils.security import safe_http_request

logger = logging.getLogger("animetix.inference.rerank_component")

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"


class RerankComponent:
    """Document reranking (Cohere API or local CrossEncoder), composable.

    Logic copied verbatim from RerankMixin; ``self._log_usage``/``self.generate``
    are replaced by the injected context. The lazy CrossEncoder cache lives here.
    """

    def __init__(
        self,
        ctx: InferenceComponentContext,
        reranker_model_name: str = DEFAULT_RERANKER_MODEL,
    ):
        self._ctx = ctx
        self._reranker_model_name = reranker_model_name
        self._cross_encoder = None

    @property
    def is_loaded(self) -> bool:
        return self._cross_encoder is not None

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []

        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                headers = {
                    "Authorization": f"Bearer {cohere_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": "rerank-multilingual-v3.0",
                    "query": query,
                    "documents": documents,
                }
                response = safe_http_request(
                    "POST",
                    "https://api.cohere.ai/v1/rerank",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    scores = [0.0] * len(documents)
                    for item in data.get("results", []):
                        idx = item.get("index")
                        if idx is not None and idx < len(scores):
                            scores[idx] = float(item.get("relevance_score", 0.0))
                    self._ctx.log_usage(engine="cohere:rerank", units=len(documents))
                    return scores
            except Exception as e:
                logger.warning(
                    f"⚠️ Cohere Rerank API failed: {e}. Falling back to local/prompt."
                )

        try:
            sentence_transformers = lazy_import("sentence_transformers")
            if self._cross_encoder is None:
                logger.info(f"🏗️ Loading CrossEncoder: {self._reranker_model_name}")
                self._cross_encoder = sentence_transformers.CrossEncoder(
                    self._reranker_model_name
                )
            pairs = [[query, doc] for doc in documents]
            scores = self._cross_encoder.predict(pairs)
            self._ctx.log_usage(engine="local:rerank", units=len(documents))
            return [float(score) for score in scores]
        except Exception as e:
            logger.error(f"❌ Local reranker failed: {e}")
            if self._ctx.generate is not None:
                logger.info("Using prompt-based reranking fallback.")
                prompt = f"Requête: {query}\n\nDocuments à évaluer:\n"
                for i, doc in enumerate(documents):
                    prompt += f"ID {i}: {doc[:500]}\n"
                prompt += "\nDonne un score de pertinence entre 0.0 et 1.0 pour chaque document. Réponds avec une liste JSON: [score0, score1, ...]"
                try:
                    raw = self._ctx.generate(
                        prompt, system_prompt="Tu es un reranker expert."
                    )
                    match = re.search(r"\[.*\]", raw)
                    if match:
                        scores = json.loads(match.group(0))
                        if len(scores) == len(documents):
                            return [float(s) for s in scores]
                except Exception as e:
                    logger.warning(f"Prompt-based reranking fallback failed: {e}")
            return [0.0] * len(documents)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/test_rerank_component.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/components/__init__.py backend/adapters/inference/components/context.py backend/adapters/inference/components/rerank_component.py tests/adapters/test_rerank_component.py
git commit -m "feat(inference): RerankComponent + InferenceComponentContext (composable rerank)"
```

---

### Task 2: MangaOcrComponent

**Files:**
- Create: `backend/adapters/inference/components/manga_ocr_component.py`
- Test: `tests/adapters/test_manga_ocr_component.py`

**Interfaces:**
- Consumes: `InferenceComponentContext` (Task 1).
- Produces: `MangaOcrComponent(ctx)` with `process_manga_page(image_data: bytes) -> dict` (keys `text`, `layout`, `status`; on error also `message`).

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_manga_ocr_component.py
import io
from unittest.mock import MagicMock

from PIL import Image

from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.components.manga_ocr_component import MangaOcrComponent


class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, engine, input_tokens=0, output_tokens=0, units=0, allocated_budget=0):
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/test_manga_ocr_component.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'adapters.inference.components.manga_ocr_component'`.

- [ ] **Step 3: Write the implementation**

Create `backend/adapters/inference/components/manga_ocr_component.py`:

```python
import logging
import os
from io import BytesIO
from typing import Any, Dict

from adapters.inference.components.context import InferenceComponentContext
from core.utils.lazy_import import lazy_import

torch = lazy_import("torch")
transformers = lazy_import("transformers")

logger = logging.getLogger("animetix.inference.manga_ocr_component")


class MangaOcrComponent:
    """Manga page OCR / text extraction, composable.

    Logic copied verbatim from MangaOcrMixin; ``self._log_usage`` is replaced by
    the injected context and the lazy pipeline cache lives on the component.
    """

    def __init__(self, ctx: InferenceComponentContext):
        self._ctx = ctx
        self._pipeline = None

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        try:
            from PIL import Image  # noqa: E402

            img = Image.open(BytesIO(image_data)).convert("RGB")

            model_id = "microsoft/trocr-base-handwritten"
            if self._pipeline is None:
                logger.info(
                    "🏗️ Loading Manga OCR (fallback to generic OCR if specialized unavailable)..."
                )
                mount_path = os.getenv("GCP_MODELS_MOUNT_PATH", "/mnt/models")
                local_model_path = os.path.join(mount_path, "manga-ocr")
                if os.path.exists(local_model_path):
                    logger.info(
                        f"📚 Loading Manga OCR from local FUSE path: {local_model_path}"
                    )
                    model_id = local_model_path

                self._pipeline = transformers.pipeline(
                    "image-to-text",
                    model=model_id,
                    device=0 if torch.cuda.is_available() else -1,
                )

            result = self._pipeline(img)
            extracted_text = result[0]["generated_text"] if result else ""

            self._ctx.log_usage(engine=f"transformers:{model_id}:ocr", units=1)

            width, height = img.size
            simulated_layout = [
                {"box": [10, 10, width // 2, height // 4], "text": extracted_text[:50]},
                {
                    "box": [width // 2, height // 4, width - 10, height // 2],
                    "text": extracted_text[50:] if len(extracted_text) > 50 else "",
                },
            ]

            return {
                "text": extracted_text,
                "layout": simulated_layout,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"❌ Manga OCR failed: {e}")
            return {"text": "", "layout": [], "status": "error", "message": str(e)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/test_manga_ocr_component.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/components/manga_ocr_component.py tests/adapters/test_manga_ocr_component.py
git commit -m "feat(inference): MangaOcrComponent (composable manga OCR)"
```

---

### Task 3: Wire components into UnifiedInferenceAdapter

**Files:**
- Modify: `backend/adapters/inference/unified_inference_adapter.py` (imports lines 8-17; class bases lines 30-40; `__init__` after line 67; add two delegating methods)
- Test: `tests/adapters/test_unified_inference_composition.py`

**Interfaces:**
- Consumes: `RerankComponent`, `MangaOcrComponent`, `InferenceComponentContext` (Tasks 1-2).
- Produces: `UnifiedInferenceAdapter` no longer inherits `MangaOcrMixin`/`RerankMixin`; holds `self._rerank`, `self._manga_ocr`; methods `rerank_documents(query, documents)` and `process_manga_page(image_data)` delegate to them.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_unified_inference_composition.py
from unittest.mock import MagicMock

from adapters.inference.components.manga_ocr_component import MangaOcrComponent
from adapters.inference.components.rerank_component import RerankComponent
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter


def _adapter():
    return UnifiedInferenceAdapter(api_base="http://x/v1", model_name="m")


def test_components_are_built_and_typed():
    a = _adapter()
    assert isinstance(a._rerank, RerankComponent)
    assert isinstance(a._manga_ocr, MangaOcrComponent)


def test_context_wired_from_adapter():
    a = _adapter()
    assert a._rerank._ctx.log_usage == a._log_usage
    assert a._rerank._ctx.generate == a.generate
    assert a._manga_ocr._ctx.log_usage == a._log_usage


def test_rerank_delegates_to_component():
    a = _adapter()
    a._rerank.rerank_documents = MagicMock(return_value=[0.5])
    assert a.rerank_documents("q", ["d"]) == [0.5]
    a._rerank.rerank_documents.assert_called_once_with("q", ["d"])


def test_manga_delegates_to_component():
    a = _adapter()
    a._manga_ocr.process_manga_page = MagicMock(return_value={"status": "success"})
    assert a.process_manga_page(b"img") == {"status": "success"}
    a._manga_ocr.process_manga_page.assert_called_once_with(b"img")


def test_no_longer_inherits_pilot_mixins():
    from adapters.inference.manga_ocr import MangaOcrMixin
    from adapters.inference.rerank_mixin import RerankMixin

    assert not issubclass(UnifiedInferenceAdapter, MangaOcrMixin)
    assert not issubclass(UnifiedInferenceAdapter, RerankMixin)


def test_capability_detection_still_routes_to_unified():
    a = _adapter()
    a.health_check = lambda: {"status": "offline"}  # avoid network in fallback init
    fb = FallbackInferenceAdapter([a])
    assert a in fb._capability_cache.get("rerank_documents", [])
    assert a in fb._capability_cache.get("process_manga_page", [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/test_unified_inference_composition.py -q`
Expected: FAIL — `AttributeError: 'UnifiedInferenceAdapter' object has no attribute '_rerank'` (and `test_no_longer_inherits_pilot_mixins` fails since it still inherits them).

- [ ] **Step 3: Write the implementation**

In `unified_inference_adapter.py`:

(a) Remove the two mixin imports (delete these two lines):

```python
from adapters.inference.manga_ocr import MangaOcrMixin
from adapters.inference.rerank_mixin import RerankMixin
```

Add the component imports next to the other inference imports:

```python
from adapters.inference.components.context import InferenceComponentContext
from adapters.inference.components.manga_ocr_component import MangaOcrComponent
from adapters.inference.components.rerank_component import RerankComponent
```

(b) Remove `MangaOcrMixin,` and `RerankMixin,` from the class bases. The declaration becomes:

```python
class UnifiedInferenceAdapter(
    ClipVisionMixin,
    DepthEstimationMixin,
    VideoAnalysisMixin,
    AudioMixin,
    ImageGenMixin,
    VlmMixin,
    InferencePort,
):
```

(c) In `__init__`, immediately after the cache init line `self._last_logprobs: List[TokenLogProb] = []` (line 67), add:

```python
        # Composed capability components (replacing MangaOcr/Rerank mixins).
        _component_ctx = InferenceComponentContext(
            log_usage=self._log_usage, generate=self.generate
        )
        self._rerank = RerankComponent(_component_ctx)
        self._manga_ocr = MangaOcrComponent(_component_ctx)
```

(d) Add two delegating methods (place them anywhere in the class body, e.g. after `__init__`):

```python
    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        return self._rerank.rerank_documents(query, documents)

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        return self._manga_ocr.process_manga_page(image_data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/test_unified_inference_composition.py -q`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/adapters/inference/unified_inference_adapter.py tests/adapters/test_unified_inference_composition.py
git commit -m "refactor(inference): UnifiedInferenceAdapter composes Rerank/MangaOcr components"
```

---

### Task 4: Verification sweep

**Files:**
- Verify only (no new product code).

- [ ] **Step 1: Run the inference + fallback suites**

Run: `python -m pytest tests/adapters tests/core/test_inference_adapters.py tests/core/test_fallback_adapter.py tests/core/test_manga_ocr_adapter.py -q -p no:cacheprovider`
Expected: PASS (pre-existing `@pytest.mark.integration` failures that need a live LLM/GPU may remain; no NEW failures introduced by this change — in particular `test_creative_inference.py`, `test_inference_adapters.py`, and the brain-api rerank/manga tests stay green because the mixins and other adapters are untouched).

If any previously-passing test newly fails, fix the cause (do not weaken the test) and re-run.

- [ ] **Step 2: Lint**

Run: `python -m ruff check backend/adapters/inference/components/ backend/adapters/inference/unified_inference_adapter.py`
Run: `python -m ruff format backend/adapters/inference/components/ backend/adapters/inference/unified_inference_adapter.py tests/adapters/test_rerank_component.py tests/adapters/test_manga_ocr_component.py tests/adapters/test_unified_inference_composition.py`
Expected: All checks passed; format clean (commit any reformat).

- [ ] **Step 3: Commit (only if ruff format changed files)**

```bash
git add -A
git commit -m "style: ruff format for inference composition pilot"
```

---

## Notes for the executor

- Do NOT touch `backend/adapters/inference/manga_ocr.py`, `rerank_mixin.py`, `vision_transformers_adapter.py`, or `local_rerank_adapter.py` — the pilot is Unified-only by design.
- The transitional duplication between the components and the mixins is intentional; the dedup (migrate the other adapters to the components, delete the mixins) is a TODO follow-up, not part of this plan.
