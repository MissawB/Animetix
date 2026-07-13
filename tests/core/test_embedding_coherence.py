"""Write/read embedding-model coherence guard.

Before this fix the catalogue vectoriser (``pipeline.models_registry``, the
writer) defaulted its text model to ``MODEL_VERSION_TEXT=v4`` ->
``Qwen/Qwen3-Embedding-8B`` (4096-d), while
``PGVectorRepositoryAdapter.embedding_fn`` (the reader, used to embed search
queries) hardcoded ``jinaai/jina-embeddings-v3`` (1024-d). Two different
models at two different dimensions can never match in pgvector -- text search
was silently dead. Both sides must resolve the active text-embedding model
through the SAME ``core.utils.model_registry`` source of truth
(``EMBEDDING_VERSIONS`` + ``MODEL_VERSION_TEXT`` env var), so changing the
version in one place changes both.
"""

from unittest.mock import MagicMock

import sentence_transformers
from adapters.persistence.pgvector_repository_adapter import PGVectorRepositoryAdapter
from core.utils.model_registry import EMBEDDING_VERSIONS
from pipeline import models_registry as mr_mod


def _patch_writer_loader(monkeypatch):
    """Intercept the SentenceTransformer construction the writer performs."""
    captured = {}

    class FakeST:
        def __init__(self, model_id, **kwargs):
            captured["model_id"] = model_id
            captured["kwargs"] = kwargs

    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", FakeST)
    monkeypatch.setattr(
        mr_mod.ModelIntegrityVerifier,
        "verify",
        staticmethod(lambda model_id, revision=None: None),
    )
    return captured


def _patch_reader_loader(mocker):
    """Intercept the SentenceTransformer construction the reader performs."""
    fake_st = MagicMock()
    mocker.patch.dict(
        "sys.modules",
        {"sentence_transformers": MagicMock(SentenceTransformer=fake_st)},
    )
    return fake_st


def test_writer_default_and_reader_resolve_same_model_id(monkeypatch, mocker, tmp_path):
    """The invariant that was violated: writer default == reader model, always."""
    monkeypatch.delenv("MODEL_VERSION_TEXT", raising=False)

    writer_captured = _patch_writer_loader(monkeypatch)
    writer_registry = mr_mod.ModelsRegistry()
    writer_registry._device = "cpu"
    _ = writer_registry.text_model
    writer_model_id = writer_captured["model_id"]

    reader_fake_st = _patch_reader_loader(mocker)
    reader_adapter = PGVectorRepositoryAdapter(project_root=str(tmp_path))
    _ = reader_adapter.embedding_fn
    reader_model_id = reader_fake_st.call_args.args[0]

    assert writer_model_id == reader_model_id
    # ... and it's the CPU-loadable, 1024-d, 1GB model the whole app agrees on.
    assert (
        writer_model_id
        == EMBEDDING_VERSIONS["text"]["v3"]
        == ("jinaai/jina-embeddings-v3")
    )


def test_env_override_changes_writer_and_reader_together(monkeypatch, mocker, tmp_path):
    """Someone with a GPU can opt into v4 -- but it must move BOTH sides at once."""
    monkeypatch.setenv("MODEL_VERSION_TEXT", "v4")

    writer_captured = _patch_writer_loader(monkeypatch)
    writer_registry = mr_mod.ModelsRegistry()  # reads env at construction time
    writer_registry._device = "cpu"
    _ = writer_registry.text_model
    writer_model_id = writer_captured["model_id"]

    reader_fake_st = _patch_reader_loader(mocker)
    reader_adapter = PGVectorRepositoryAdapter(project_root=str(tmp_path))
    _ = reader_adapter.embedding_fn
    reader_model_id = reader_fake_st.call_args.args[0]

    assert (
        writer_model_id
        == reader_model_id
        == EMBEDDING_VERSIONS["text"]["v4"]
        == ("Qwen/Qwen3-Embedding-8B")
    )
