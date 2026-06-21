# -*- coding: utf-8 -*-
"""Behavior tests for the Late Interaction ColBERT reranker adapter.

Target: ``adapters.persistence.colbert_adapter.LateInteractionColBERTAdapter``.

All heavy ops are mocked: the Hugging Face ``AutoModel`` / ``AutoTokenizer``
loaders are patched in the ``transformers`` namespace (the module does a fresh
``from transformers import ...`` inside ``_lazy_init``), and the real-embedding
path is exercised by injecting fake model/tokenizer objects that return small
deterministic tensors. No weights are loaded, no network, no GPU.

Assertions check the REAL reranked output (ordering by MaxSim score, scores,
top-k via slicing, empty input) rather than bare mock-call counts.
"""

import numpy as np
import pytest
from adapters.persistence.colbert_adapter import LateInteractionColBERTAdapter


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _force_fallback(monkeypatch):
    """Make ``from transformers import ...`` raise so the adapter takes the
    deterministic numpy simulation path (model/tokenizer stay None)."""
    import transformers

    def _boom(*a, **k):
        raise OSError("offline / no weights in test")

    monkeypatch.setattr(transformers, "AutoModel", _boom, raising=False)
    monkeypatch.setattr(transformers, "AutoTokenizer", _boom, raising=False)


def _orthonormal_rows(*rows):
    """Return a (N, D) array whose rows are the given small vectors L2-normalised.
    Used to make MaxSim scores analytically predictable."""
    arr = np.array(rows, dtype=np.float64)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


# --------------------------------------------------------------------------- #
# Construction / defaults
# --------------------------------------------------------------------------- #
def test_init_defaults_and_lazy_state():
    a = LateInteractionColBERTAdapter()
    assert a.model_name == "colbert-ir/colbertv2.0"
    assert a.dimension == 128
    # Nothing loaded until first use.
    assert a._model is None
    assert a._tokenizer is None
    assert a._initialized is False


def test_init_custom_params():
    a = LateInteractionColBERTAdapter(model_name="my/model", dimension=8)
    assert a.model_name == "my/model"
    assert a.dimension == 8


# --------------------------------------------------------------------------- #
# Lazy init: success path (real HF loaders mocked) + caching
# --------------------------------------------------------------------------- #
def test_lazy_init_loads_models_and_caches(monkeypatch):
    import transformers

    fake_model = object()
    fake_tok = object()
    calls = {"model": 0, "tok": 0}

    def _load_model(name, revision="main"):
        calls["model"] += 1
        assert name == "colbert-ir/colbertv2.0"
        assert revision == "main"
        return fake_model

    def _load_tok(name, revision="main"):
        calls["tok"] += 1
        return fake_tok

    monkeypatch.setattr(
        transformers,
        "AutoModel",
        type("M", (), {"from_pretrained": staticmethod(_load_model)}),
    )
    monkeypatch.setattr(
        transformers,
        "AutoTokenizer",
        type("T", (), {"from_pretrained": staticmethod(_load_tok)}),
    )

    a = LateInteractionColBERTAdapter()
    a._lazy_init()
    assert a._initialized is True
    assert a._model is fake_model
    assert a._tokenizer is fake_tok
    assert calls == {"model": 1, "tok": 1}

    # Second call is cached: no further loads.
    a._lazy_init()
    assert calls == {"model": 1, "tok": 1}


def test_lazy_init_fallback_on_load_error(monkeypatch):
    """When HF loaders raise, the adapter must mark itself initialized but leave
    model/tokenizer as None so the deterministic simulation is used."""
    _force_fallback(monkeypatch)
    a = LateInteractionColBERTAdapter()
    a._lazy_init()
    assert a._initialized is True
    assert a._model is None
    assert a._tokenizer is None


# --------------------------------------------------------------------------- #
# Deterministic simulation embeddings (fallback)
# --------------------------------------------------------------------------- #
def test_embed_simulation_shape_and_determinism(monkeypatch):
    _force_fallback(monkeypatch)
    a = LateInteractionColBERTAdapter(dimension=16)

    e1 = a.tokenize_and_embed("red fox jumps")
    e2 = a.tokenize_and_embed("red fox jumps")
    # 3 tokens -> 3 rows, dimension cols.
    assert e1.shape == (3, 16)
    # Same input -> identical embedding (hash-seeded determinism).
    assert np.allclose(e1, e2)
    # Each token vector is L2-normalised.
    assert np.allclose(np.linalg.norm(e1, axis=1), 1.0)


def test_embed_simulation_empty_text_uses_placeholder(monkeypatch):
    _force_fallback(monkeypatch)
    a = LateInteractionColBERTAdapter(dimension=8)
    e = a.tokenize_and_embed("   ")  # whitespace splits to no words
    # Falls back to a single "empty" token row.
    assert e.shape == (1, 8)


# --------------------------------------------------------------------------- #
# Real-embedding path (model + tokenizer injected, torch real but no weights)
# --------------------------------------------------------------------------- #
def _wire_real_path(a, monkeypatch, hidden):
    """Inject fake tokenizer/model returning ``hidden`` as last_hidden_state[0]."""
    import torch

    a._initialized = True
    a._tokenizer = lambda text, **kw: {"input_ids": torch.tensor([[1, 2]])}

    class _Out:
        # last_hidden_state[0] -> (tokens, hidden_dim) tensor
        last_hidden_state = torch.tensor([hidden], dtype=torch.float32)

    class _Model:
        def __call__(self, **inputs):
            return _Out()

    a._model = _Model()


def test_real_path_projects_and_normalises(monkeypatch):
    a = LateInteractionColBERTAdapter(dimension=2)
    # hidden dim 4 -> sliced to first 2 dims, then L2 normalised per row.
    hidden = [[3.0, 4.0, 9.0, 9.0], [0.0, 5.0, 1.0, 1.0]]
    _wire_real_path(a, monkeypatch, hidden)

    e = a.tokenize_and_embed("anything")
    # Sliced to dimension=2, so shape (2 tokens, 2 dims).
    assert e.shape == (2, 2)
    # Row 0 was [3,4] -> /5 -> [0.6, 0.8]; row 1 [0,5] -> [0,1].
    assert np.allclose(e[0], [0.6, 0.8])
    assert np.allclose(e[1], [0.0, 1.0])


def test_real_path_exception_falls_back_to_simulation(monkeypatch):
    """If the real forward pass raises, the code logs and drops to the numpy
    simulation rather than propagating."""
    a = LateInteractionColBERTAdapter(dimension=8)
    a._initialized = True
    a._tokenizer = lambda text, **kw: {"input_ids": object()}

    class _BadModel:
        def __call__(self, **inputs):
            raise RuntimeError("forward exploded")

    a._model = _BadModel()

    e = a.tokenize_and_embed("two words")
    # Simulation path: 2 tokens, dimension cols, normalised rows.
    assert e.shape == (2, 8)
    assert np.allclose(np.linalg.norm(e, axis=1), 1.0)


# --------------------------------------------------------------------------- #
# MaxSim scoring
# --------------------------------------------------------------------------- #
def test_maxsim_known_value():
    a = LateInteractionColBERTAdapter()
    # Query tokens identical to two doc tokens -> each query token max-sim 1.0.
    q = _orthonormal_rows([1.0, 0.0], [0.0, 1.0])
    d = _orthonormal_rows([1.0, 0.0], [0.0, 1.0])
    # Sum of per-query max cosine = 1.0 + 1.0 = 2.0.
    assert a.calculate_maxsim(q, d) == pytest.approx(2.0)


def test_maxsim_orthogonal_query_doc():
    a = LateInteractionColBERTAdapter()
    q = _orthonormal_rows([1.0, 0.0])
    d = _orthonormal_rows([0.0, 1.0])
    # Orthogonal -> dot product 0.
    assert a.calculate_maxsim(q, d) == pytest.approx(0.0)


def test_maxsim_empty_inputs_return_zero():
    a = LateInteractionColBERTAdapter()
    empty = np.array([])
    some = _orthonormal_rows([1.0, 0.0])
    assert a.calculate_maxsim(empty, some) == 0.0
    assert a.calculate_maxsim(some, empty) == 0.0
    assert a.calculate_maxsim(empty, empty) == 0.0


# --------------------------------------------------------------------------- #
# rank_documents: real ordering, scores, field selection, empty input
# --------------------------------------------------------------------------- #
def test_rank_documents_empty_returns_empty():
    a = LateInteractionColBERTAdapter()
    assert a.rank_documents("query", []) == []


def test_rank_documents_orders_by_real_maxsim_score(monkeypatch):
    """Drive ranking with controlled embeddings so the resulting order and
    scores are analytically known (not just 'sort was called')."""
    a = LateInteractionColBERTAdapter()

    # Query has a single token e1.
    q = _orthonormal_rows([1.0, 0.0])
    # Doc embeddings: low (orthogonal), high (identical), mid (45 degrees).
    embeddings = {
        "low": _orthonormal_rows([0.0, 1.0]),  # maxsim 0.0
        "high": _orthonormal_rows([1.0, 0.0]),  # maxsim 1.0
        "mid": _orthonormal_rows([1.0, 1.0]),  # maxsim ~0.7071
        "QUERY": q,
    }

    def fake_embed(text):
        return embeddings[text]

    monkeypatch.setattr(a, "tokenize_and_embed", fake_embed)

    docs = [
        {"description": "low", "id": "L"},
        {"description": "high", "id": "H"},
        {"description": "mid", "id": "M"},
    ]
    # Query string is "QUERY"; docs are looked up by their description text.
    ranked = a.rank_documents("QUERY", docs)

    # Real descending order by score: high > mid > low.
    assert [d["id"] for d in ranked] == ["H", "M", "L"]
    assert ranked[0]["colbert_score"] == pytest.approx(1.0)
    assert ranked[1]["colbert_score"] == pytest.approx(np.sqrt(0.5))
    assert ranked[2]["colbert_score"] == pytest.approx(0.0)


def test_rank_documents_does_not_mutate_input(monkeypatch):
    a = LateInteractionColBERTAdapter()
    q = _orthonormal_rows([1.0, 0.0])
    monkeypatch.setattr(a, "tokenize_and_embed", lambda t: q)
    original = {"description": "doc text"}
    docs = [original]
    ranked = a.rank_documents("q", docs)
    # Original untouched; only the copy carries the score.
    assert "colbert_score" not in original
    assert "colbert_score" in ranked[0]
    assert ranked[0] is not original


def test_rank_documents_field_fallback_to_title(monkeypatch):
    """When the requested text_field is absent, the code falls back to 'title'.
    A doc with no matching text yields empty embeddings -> score 0.0, so it
    ranks last."""
    a = LateInteractionColBERTAdapter()
    q = _orthonormal_rows([1.0, 0.0])

    def fake_embed(text):
        if text == "good title":
            return _orthonormal_rows([1.0, 0.0])  # maxsim 1.0 vs query
        if text == "":
            return np.array([])  # no text -> empty -> score 0
        return q  # the query itself

    monkeypatch.setattr(a, "tokenize_and_embed", fake_embed)

    docs = [
        {"title": "good title", "id": "withtitle"},  # no 'description' -> uses title
        {"other": "x", "id": "notext"},  # no description, no title -> ""
    ]
    ranked = a.rank_documents("q", docs, text_field="description")
    assert [d["id"] for d in ranked] == ["withtitle", "notext"]
    assert ranked[0]["colbert_score"] == pytest.approx(1.0)
    assert ranked[-1]["colbert_score"] == 0.0


def test_rank_documents_topk_via_slicing(monkeypatch):
    """The adapter returns a fully ranked list; callers take top-k by slicing.
    Verify the slice yields the true highest-scoring documents in order."""
    a = LateInteractionColBERTAdapter()

    scores = {"a": 0.1, "b": 0.9, "c": 0.5, "d": 0.7}

    def fake_embed(text):
        if text == "Q":
            return _orthonormal_rows([1.0, 0.0])
        # Encode the desired maxsim as cos(theta) by choosing a vector whose
        # dot with [1,0] equals the target score.
        s = scores[text]
        return _orthonormal_rows([s, np.sqrt(max(0.0, 1 - s * s))])

    monkeypatch.setattr(a, "tokenize_and_embed", fake_embed)

    docs = [{"description": k, "id": k} for k in scores]
    ranked = a.rank_documents("Q", docs)
    top2 = ranked[:2]
    assert [d["id"] for d in top2] == ["b", "d"]
    assert top2[0]["colbert_score"] == pytest.approx(0.9)
    assert top2[1]["colbert_score"] == pytest.approx(0.7)
