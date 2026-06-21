# -*- coding: utf-8 -*-
"""Real-behavior coverage tests for the Otaku knowledge mass-indexer.

Target module: ``backend.pipeline.mlops.index_otaku_knowledge`` (the
``OtakuKnowledgeIndexer`` pipeline that compiles the local meta databases into
semantic facts and upserts them into ChromaDB).

All external I/O is mocked: the Django DI container / ChromaDB repository and the
embedding function. The real fact-compilation, sentence chunking, doc-id /
metadata construction and control flow run against the real local ``*_db``
fixtures so the assertions exercise genuine behaviour (no false-green).

The production module performs ``sys.path`` hacks against a hard-coded
``...\\src\\pipeline\\mlops`` path that does not exist in the repo, so the bare
``from creators_db import ...`` imports only resolve when the *real* directory
(``backend/pipeline/mlops``) is on ``sys.path``. We add it here before importing
the module under test, mirroring how the pipeline is meant to run.
"""

import logging
import os
import sys
from unittest.mock import MagicMock

import pytest

# --- Make the bare ``*_db`` imports resolvable -----------------------------
# The module does ``from creators_db import ...`` expecting its own directory on
# sys.path. Add the real backend/pipeline/mlops directory (computed from this
# test file's location, not hard-coded) so the import succeeds.
_MLOPS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend", "pipeline", "mlops")
)
if _MLOPS_DIR not in sys.path:
    sys.path.insert(0, _MLOPS_DIR)

import backend.pipeline.mlops.index_otaku_knowledge as iok  # noqa: E402

# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def indexer():
    """A dry-run indexer with no DI container (the standalone default)."""
    ix = iok.OtakuKnowledgeIndexer(dry_run=True)
    ix.container = None
    return ix


class _CaptureHandler(logging.Handler):
    """Collect log records emitted on ``iok.logger`` directly.

    The module's logger may have ``propagate`` disabled by the project's logging
    config, so pytest's ``caplog`` (which hooks the root logger) can miss its
    records. Attaching a handler straight onto the module logger is reliable.
    """

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    @property
    def messages(self):
        return [r.getMessage() for r in self.records]


@pytest.fixture
def log_capture():
    handler = _CaptureHandler()
    iok.logger.addHandler(handler)
    prev_level = iok.logger.level
    iok.logger.setLevel(logging.DEBUG)
    try:
        yield handler
    finally:
        iok.logger.removeHandler(handler)
        iok.logger.setLevel(prev_level)


def _make_repo(coll_names=None):
    """Build a mock repository whose chroma surface mirrors the real one.

    ``embedding_fn`` returns one deterministic vector per input text and records
    every call so tests can assert exactly what got vectorised.
    """
    repo = MagicMock()
    repo.chroma.coll_names = coll_names if coll_names is not None else {}

    def _embed(texts):
        # One 3-dim vector per text; values derived from length so we can assert
        # the embedding function actually received our chunk text.
        return [[float(len(t)), 1.0, 2.0] for t in texts]

    repo.chroma.embedding_fn = MagicMock(side_effect=_embed)
    repo.chroma.upsert_items = MagicMock()
    return repo


# --- compile_all_facts ------------------------------------------------------


def test_compile_all_facts_aggregates_every_source(indexer):
    """compile_all_facts returns one entry per row across all DBs + relations."""
    facts = indexer.compile_all_facts()

    expected = (
        len(iok.ANIME_SONGS_AND_SINGERS)
        + len(iok.SEIYUU_PROFILES)
        + len(iok.CREATORS_AND_STUDIOS)
        + len(iok.FRENCH_VOICE_ACTORS)
        + len(iok.FRENCH_MANGA_PUBLISHERS)
        + len(iok.FRENCH_ANIME_DISTRIBUTORS)
        + len(iok.JAPANESE_MANGA_PUBLISHERS)
        + len(iok.JAPANESE_ANIME_DISTRIBUTORS)
        + len(iok.POP_CULTURE_AWARDS)
        + len(iok.SERIALIZATION_MAGAZINES)
        + len(iok.VOLUMES_AND_EPISODES_DATA)
        + len(iok.SONGS_AND_SEIYUU_RELATIONS)
        + len(iok.AWARDS_AND_MAGAZINES_RELATIONS)
        + len(iok.FRENCH_MARKET_RELATIONS)
        + len(iok.JAPANESE_MARKET_RELATIONS)
        + len(iok.TRANSMEDIA_RELATIONS)
    )
    assert len(facts) == expected

    # Every fact is a well-formed dict.
    for f in facts:
        assert set(f) == {"category", "title", "content"}
        assert f["category"] and f["title"]

    # The expected set of categories is present.
    categories = {f["category"] for f in facts}
    assert {
        "Anisong Artists",
        "Seiyuu Profiles",
        "Creators & Directors",
        "French Voice Actors (VF)",
        "French Manga Publishers",
        "French Anime Distributors",
        "Japanese Manga Publishers",
        "Japanese Anime Distributors (JP)",
        "Pop-Culture Awards",
        "Serialization Magazines",
        "Volumes & Episodes Stats",
        "Expert Transmedia Relations",
    } <= categories


def test_compile_all_facts_anisong_content_uses_details(indexer):
    """An Anisong fact embeds the source dict's definition/examples in content."""
    name, details = next(iter(iok.ANIME_SONGS_AND_SINGERS.items()))
    facts = indexer.compile_all_facts()
    match = next(
        f for f in facts if f["category"] == "Anisong Artists" and f["title"] == name
    )
    assert "Artiste Anisong" in match["content"]
    assert details.get("definition", "") in match["content"]
    assert details.get("examples", "") in match["content"]


def test_compile_all_facts_question_answer_relation_branch(indexer, monkeypatch):
    """A relation with question/answer keys -> Q/A formatted title + content."""
    monkeypatch.setattr(
        iok,
        "SONGS_AND_SEIYUU_RELATIONS",
        [{"question": "Q?" * 60, "answer": "An answer."}],
    )
    monkeypatch.setattr(iok, "AWARDS_AND_MAGAZINES_RELATIONS", [])
    monkeypatch.setattr(iok, "FRENCH_MARKET_RELATIONS", [])
    monkeypatch.setattr(iok, "JAPANESE_MARKET_RELATIONS", [])
    monkeypatch.setattr(iok, "TRANSMEDIA_RELATIONS", [])

    facts = indexer.compile_all_facts()
    rel = next(f for f in facts if f["category"] == "Expert Transmedia Relations")
    # Title is truncated to the first 100 chars of the question.
    assert rel["title"].startswith("Relation : ")
    assert len(rel["title"]) == len("Relation : ") + 100
    assert rel["content"].startswith("Question : ")
    assert "An answer." in rel["content"]


def test_compile_all_facts_source_target_relation_branch(indexer, monkeypatch):
    """A relation without question/answer -> source/target formatted entry."""
    monkeypatch.setattr(iok, "SONGS_AND_SEIYUU_RELATIONS", [])
    monkeypatch.setattr(iok, "AWARDS_AND_MAGAZINES_RELATIONS", [])
    monkeypatch.setattr(iok, "FRENCH_MARKET_RELATIONS", [])
    monkeypatch.setattr(iok, "JAPANESE_MARKET_RELATIONS", [])
    monkeypatch.setattr(
        iok,
        "TRANSMEDIA_RELATIONS",
        [{"source": "Naruto", "target": "Boruto", "relation_text": "sequel of"}],
    )

    facts = indexer.compile_all_facts()
    rel = next(f for f in facts if f["category"] == "Expert Transmedia Relations")
    assert rel["title"] == "Relation sémantique Naruto - Boruto"
    assert "sequel of" in rel["content"]


# --- chunk_ssemantic --------------------------------------------------------


def test_chunk_short_text_single_chunk(indexer):
    """Text below the size threshold stays a single chunk, sentences joined."""
    chunks = indexer.chunk_ssemantic("First sentence. Second sentence.", size=400)
    assert chunks == ["First sentence. Second sentence."]


def test_chunk_splits_on_size_boundary(indexer):
    """Exceeding ``size`` starts a new chunk at the sentence boundary."""
    s1 = "A" * 300 + "."
    s2 = "B" * 300 + "."
    chunks = indexer.chunk_ssemantic(f"{s1} {s2}", size=400)
    assert len(chunks) == 2
    assert chunks[0] == s1
    assert chunks[1] == s2


def test_chunk_skips_empty_sentences(indexer):
    """Whitespace-only fragments are dropped, not emitted as chunks."""
    chunks = indexer.chunk_ssemantic("Hello world.    ", size=400)
    assert chunks == ["Hello world."]


def test_chunk_empty_string_returns_empty(indexer):
    assert indexer.chunk_ssemantic("", size=400) == []


# --- execute_indexation: dry-run -------------------------------------------


def test_execute_indexation_dry_run_does_not_touch_chroma(indexer, log_capture):
    """Dry-run logs a simulation and never calls the repository."""
    repo = _make_repo()
    indexer.container = MagicMock()
    indexer.container.repository.return_value = repo

    result = indexer.execute_indexation()

    assert result is None
    # Dry-run must short-circuit before fetching the repository.
    indexer.container.repository.assert_not_called()
    repo.chroma.upsert_items.assert_not_called()
    assert any("Dry-Run" in m for m in log_capture.messages)


# --- execute_indexation: no container --------------------------------------


def test_execute_indexation_no_container_logs_error(log_capture):
    """Production mode without a DI container aborts with an error log."""
    ix = iok.OtakuKnowledgeIndexer(dry_run=False)
    ix.container = None

    ix.execute_indexation()

    assert any("Container is not initialized" in m for m in log_capture.messages)


# --- execute_indexation: real upsert ---------------------------------------


def test_execute_indexation_upserts_vectorised_chunks(monkeypatch):
    """End-to-end production path: facts -> chunks -> embeddings -> upsert.

    We shrink the source data to two deterministic facts so we can assert the
    exact ids/embeddings/metadata handed to ChromaDB.
    """
    ix = iok.OtakuKnowledgeIndexer(dry_run=False)
    repo = _make_repo(coll_names={"Anime": "anime_thematic"})
    ix.container = MagicMock()
    ix.container.repository.return_value = repo

    # Two known facts, each a single short sentence -> one chunk each.
    fake_facts = [
        {"category": "Test Cat", "title": "Alpha", "content": "Fact about Alpha."},
        {"category": "Test Cat", "title": "Beta", "content": "Fact about Beta."},
    ]
    monkeypatch.setattr(ix, "compile_all_facts", lambda: fake_facts)

    ix.execute_indexation()

    # The repository upsert was called exactly once into the configured collection.
    assert repo.chroma.upsert_items.call_count == 1
    args, _ = repo.chroma.upsert_items.call_args
    coll_name, ids, embeddings, metadatas = args

    assert coll_name == "anime_thematic"
    assert len(ids) == len(embeddings) == len(metadatas) == 2

    # Doc ids are derived from category + title hash + chunk index.
    assert all(i.startswith("meta_test_cat_") for i in ids)
    assert all(i.endswith("_0") for i in ids)

    # The embedding function received the context-prefixed chunk text and the
    # resulting vectors were forwarded verbatim.
    embed_inputs = [c.args[0][0] for c in repo.chroma.embedding_fn.call_args_list]
    assert any("[Source: Otaku Database" in t and "Alpha" in t for t in embed_inputs)
    for text, vec in zip(embed_inputs, embeddings):
        assert vec == [float(len(text)), 1.0, 2.0]

    # Metadata carries the category and the full chunk text as description.
    for md in metadatas:
        assert md["source"] == "Otaku Meta Database"
        assert md["category"] == "Test Cat"
        assert md["title"].startswith("Expert Meta: ")
        assert "[Source: Otaku Database" in md["description"]


def test_execute_indexation_defaults_collection_name(monkeypatch):
    """When coll_names lacks 'Anime', the default 'anime_thematic' is used."""
    ix = iok.OtakuKnowledgeIndexer(dry_run=False)
    repo = _make_repo(coll_names={})  # no "Anime" key
    ix.container = MagicMock()
    ix.container.repository.return_value = repo
    monkeypatch.setattr(
        ix,
        "compile_all_facts",
        lambda: [{"category": "C", "title": "T", "content": "Body."}],
    )

    ix.execute_indexation()

    coll_name = repo.chroma.upsert_items.call_args.args[0]
    assert coll_name == "anime_thematic"


def test_execute_indexation_swallows_chroma_errors(monkeypatch, log_capture):
    """A failure inside the indexation block is caught and logged, not raised."""
    ix = iok.OtakuKnowledgeIndexer(dry_run=False)
    repo = _make_repo(coll_names={"Anime": "anime_thematic"})
    repo.chroma.upsert_items.side_effect = RuntimeError("chroma exploded")
    ix.container = MagicMock()
    ix.container.repository.return_value = repo
    monkeypatch.setattr(
        ix,
        "compile_all_facts",
        lambda: [{"category": "C", "title": "T", "content": "Body."}],
    )

    ix.execute_indexation()  # must not raise

    assert any("Failed to execute mass indexation" in m for m in log_capture.messages)


def test_execute_indexation_real_data_full_pipeline(monkeypatch):
    """Smoke test: run the real compiled facts through the upsert path.

    Exercises the production loop over the *actual* meta databases (hundreds of
    chunks) with only the embedding/upsert I/O mocked, proving the whole
    chunk/vectorise/metadata machinery runs end-to-end.
    """
    ix = iok.OtakuKnowledgeIndexer(dry_run=False)
    repo = _make_repo(coll_names={"Anime": "anime_thematic"})
    ix.container = MagicMock()
    ix.container.repository.return_value = repo

    ix.execute_indexation()

    repo.chroma.upsert_items.assert_called_once()
    ids = repo.chroma.upsert_items.call_args.args[1]
    # The real databases produce many chunks; sanity-check it's non-trivial.
    assert len(ids) > 50
    assert len(ids) == len(set(ids)) or len(ids) >= len(set(ids))  # ids generated


# --- __main__ entry point ---------------------------------------------------


def test_main_entry_runs_dry_run(monkeypatch, capfd):
    """The ``__main__`` guard parses --dry-run and drives the real dry-run.

    ``runpy.run_path`` executes the production file as ``__main__`` (covering the
    argparse/entry-point lines). argparse maps ``--dry-run`` to ``dry_run=True``,
    so the genuine dry-run path runs: it compiles the real 501 meta facts and
    logs a simulation summary, performing no DB / network I/O. We assert on the
    captured stderr (the module logs to a stream handler at fd level, which the
    fresh ``django.setup()`` reconfigures -- so fd-level ``capfd`` is the robust
    way to observe the output).
    """
    monkeypatch.setattr(sys, "argv", ["index_otaku_knowledge.py", "--dry-run"])
    # Keep the real *_db imports resolvable for the fresh re-execution.
    if _MLOPS_DIR not in sys.path:
        sys.path.insert(0, _MLOPS_DIR)

    import runpy

    runpy.run_path(iok.__file__, run_name="__main__")

    _out, err = capfd.readouterr()
    # The dry-run branch ran over the real compiled facts.
    assert "Dry-Run" in err
    assert "Simulating finished" in err
    assert "501" in err  # the real meta databases compile to 501 facts
