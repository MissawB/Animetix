# RAG Cognitive-Boosters Toggle + Ablation Harness — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the quantum/neuromorphic cognitive boosters in `AdvancedRAGService` switchable (config default + runtime), and add a management command that measures their effect via RAGAS (boosters ON vs OFF) so the keep/demote decision becomes data-driven.

**Architecture:** A single toggle chokepoint in `_get_cognitive_models` (returns no-op models when disabled), a context-exposing variant of `generate_advanced_answer` for the judge, and an in-process `run_rag_ablation` Django management command that re-runs the pipeline both ways per query and prints a per-metric delta table.

**Tech Stack:** Python 3.12, Django management commands, dependency-injector DI, pytest, numpy (existing booster math), the project's own `RagasEvalService` (LLM-as-judge).

## Global Constraints

- Production default stays **ON**: `cognitive_boosters_enabled` defaults to `True` everywhere.
- `generate_advanced_answer(query, media_type, user_id=None) -> str` public signature/behavior unchanged.
- The domain service stays framework-free (no Django import in `advanced_rag_service.py`); the default comes from settings via the DI container only.
- All new tests run in CI with **no live LLM** (mock the inference engine / judge).
- Spec: `docs/specs/2026-06-22-rag-cognitive-boosters-ablation-design.md`.

---

### Task 1: Runtime toggle on AdvancedRAGService

**Files:**
- Modify: `backend/core/domain/services/advanced_rag_service.py` (constructor ~46-74, `_get_cognitive_models` ~76-88)
- Test: `tests/core/test_advanced_rag_cognitive_toggle.py`

**Interfaces:**
- Produces: `AdvancedRAGService(..., cognitive_boosters_enabled: bool = True)`; attribute `self.cognitive_boosters_enabled`; method `set_cognitive_boosters(enabled: bool) -> None`. When disabled, `_get_cognitive_models(...)` returns `(None, None, None)` and `_adjust_scores_cognitively` is a no-op.

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_advanced_rag_cognitive_toggle.py
from unittest.mock import MagicMock

from core.domain.services.advanced_rag_service import AdvancedRAGService


def _svc(enabled=True):
    return AdvancedRAGService(
        repository=MagicMock(),
        llm_service=MagicMock(),
        cognitive_boosters_enabled=enabled,
    )


def test_disabled_boosters_make_adjust_a_noop():
    svc = _svc(enabled=False)
    cands = [{"id": "1", "score": 0.5, "genres": ["shonen"]}]
    out = svc._adjust_scores_cognitively([dict(cands[0])], "shonen action")
    assert out == cands
    assert "cognitive_boost" not in out[0]


def test_enabled_boosters_apply_boost():
    svc = _svc(enabled=True)
    cands = [{"id": "1", "score": 0.5, "genres": ["shonen"]}]
    out = svc._adjust_scores_cognitively(cands, "shonen action")
    assert "cognitive_boost" in out[0]


def test_set_cognitive_boosters_flips_at_runtime():
    svc = _svc(enabled=True)
    svc.set_cognitive_boosters(False)
    cands = [{"id": "1", "score": 0.5, "genres": ["shonen"]}]
    out = svc._adjust_scores_cognitively([dict(cands[0])], "shonen")
    assert out == cands
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/core/test_advanced_rag_cognitive_toggle.py -q`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'cognitive_boosters_enabled'`.

- [ ] **Step 3: Write minimal implementation**

In `advanced_rag_service.py`, add the parameter to `__init__` (after `cache_port`):

```python
        cache_port: Optional[CachePort] = None,
        cognitive_boosters_enabled: bool = True,
    ):
```

Store it (near the other assignments, after `self.cache = ...`):

```python
        self.cognitive_boosters_enabled = cognitive_boosters_enabled
```

Add the chokepoint as the first lines of `_get_cognitive_models`:

```python
    def _get_cognitive_models(
        self, user_id: Optional[str] = None
    ) -> Tuple[Any, Any, Any]:
        """Charge ou initialise les modèles cognitifs spécifiques à l'utilisateur."""
        if not self.cognitive_boosters_enabled:
            return None, None, None
        # 1. Gestion des modèles injectés (ou désactivés via None)
        q = self._injected_quantum
```

Add the runtime switch method (right after `_get_cognitive_models`):

```python
    def set_cognitive_boosters(self, enabled: bool) -> None:
        """Active/désactive les boosters cognitifs à chaud (utilisé par l'ablation)."""
        self.cognitive_boosters_enabled = enabled
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/core/test_advanced_rag_cognitive_toggle.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/advanced_rag_service.py tests/core/test_advanced_rag_cognitive_toggle.py
git commit -m "feat(rag): runtime toggle for cognitive boosters (default on)"
```

---

### Task 2: Expose context — generate_advanced_answer_with_context

**Files:**
- Modify: `backend/core/domain/services/advanced_rag_service.py` (`generate_advanced_answer` ~295-319)
- Test: `tests/core/test_advanced_rag_with_context.py`

**Interfaces:**
- Consumes: `AdvancedRAGService` from Task 1.
- Produces: `generate_advanced_answer_with_context(query, media_type, user_id=None) -> tuple[str, str]` returning `(answer, context)`. `generate_advanced_answer` returns only `answer` (unchanged contract).

- [ ] **Step 1: Write the failing test**

```python
# tests/core/test_advanced_rag_with_context.py
from unittest.mock import MagicMock

from core.domain.services.advanced_rag_service import AdvancedRAGService


def _svc():
    s = AdvancedRAGService(repository=MagicMock(), llm_service=MagicMock())
    s.colbert_adapter = None
    s.prompt_manager = MagicMock()
    s.prompt_manager.get_prompt.return_value = ("p", "s")
    s.llm_service.inference_engine.generate.return_value = MagicMock(text="ANSWER")
    s.hybrid_search = MagicMock(
        return_value=[{"id": "1", "title": "Naruto", "description": "ninja boy"}]
    )
    s.rerank_results = MagicMock(
        return_value=[{"id": "1", "title": "Naruto", "description": "ninja boy"}]
    )
    return s


def test_with_context_returns_answer_and_context():
    svc = _svc()
    answer, context = svc.generate_advanced_answer_with_context("q", "Anime")
    assert answer == "ANSWER"
    assert "Naruto" in context


def test_generate_advanced_answer_returns_only_answer():
    svc = _svc()
    svc.generate_advanced_answer_with_context = MagicMock(return_value=("A", "ctx"))
    assert svc.generate_advanced_answer("q", "Anime") == "A"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/core/test_advanced_rag_with_context.py -q`
Expected: FAIL — `AttributeError: ... has no attribute 'generate_advanced_answer_with_context'`.

- [ ] **Step 3: Write minimal implementation**

Replace the body of `generate_advanced_answer` with a wrapper and add the new method:

```python
    def generate_advanced_answer(
        self, query: str, media_type: str, user_id: Optional[str] = None
    ) -> str:
        answer, _ = self.generate_advanced_answer_with_context(
            query, media_type, user_id=user_id
        )
        return answer

    def generate_advanced_answer_with_context(
        self, query: str, media_type: str, user_id: Optional[str] = None
    ) -> Tuple[str, str]:
        candidates = self.hybrid_search(query, media_type, limit=20, user_id=user_id)
        if self.colbert_adapter:
            candidates = self.colbert_adapter.rank_documents(query, candidates)
        ranked_candidates = self.rerank_results(query, candidates, user_id=user_id)
        top_results = ranked_candidates[:5]
        context = "\n".join(
            [
                f"- {r.get('title')}: {r.get('description', '')[:500]}"
                for r in top_results
            ]
        )
        if self.prompt_manager is None:
            logger.error("No prompt_manager configured; cannot generate answer.")
            return "", context
        prompt, system_prompt = self.prompt_manager.get_prompt(
            "advanced_rag_generate", context=context, query=query
        )
        inference_res = self.llm_service.inference_engine.generate(
            prompt, system_prompt=system_prompt
        )
        return inference_res.text, context
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/core/test_advanced_rag_with_context.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/advanced_rag_service.py tests/core/test_advanced_rag_with_context.py
git commit -m "refactor(rag): expose (answer, context) via generate_advanced_answer_with_context"
```

---

### Task 3: Production default from settings (DI wiring)

**Files:**
- Modify: `backend/api/animetix_project/settings.py` (add the flag, near other feature flags)
- Modify: `backend/api/animetix/containers/agentic.py` (`rag_service` provider, lines 26-33; add `from django.conf import settings` if absent)
- Test: `tests/backend/test_cognitive_boosters_setting.py`

**Interfaces:**
- Consumes: `AdvancedRAGService(cognitive_boosters_enabled=...)` from Task 1.
- Produces: setting `RAG_COGNITIVE_BOOSTERS_ENABLED` (bool, default True); the DI `rag_service` provider passes it through.

- [ ] **Step 1: Write the failing test**

```python
# tests/backend/test_cognitive_boosters_setting.py
from django.conf import settings


def test_cognitive_boosters_setting_defaults_true():
    assert getattr(settings, "RAG_COGNITIVE_BOOSTERS_ENABLED") is True


def test_rag_service_provider_wires_the_flag():
    from animetix.containers import get_container

    rag = get_container().agentic.rag_service()
    assert rag.cognitive_boosters_enabled is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_cognitive_boosters_setting.py -q`
Expected: FAIL — `AttributeError: 'Settings' object has no attribute 'RAG_COGNITIVE_BOOSTERS_ENABLED'`.

- [ ] **Step 3: Write minimal implementation**

In `settings.py` (near other `os.environ`-driven flags), add:

```python
RAG_COGNITIVE_BOOSTERS_ENABLED = os.environ.get(
    "RAG_COGNITIVE_BOOSTERS_ENABLED", "true"
).lower() in ("1", "true", "yes")
```

In `agentic.py`, ensure the settings import exists at the top (add if missing):

```python
from django.conf import settings
```

Add the kwarg to the `rag_service` provider (lines 26-33):

```python
    rag_service = providers.Singleton(
        LazyClass("core.domain.services.advanced_rag_service", "AdvancedRAGService"),
        repository=persistence.repository,
        llm_service=llm_service,
        neo4j_manager=persistence.graph_persistence_port,
        colbert_adapter=persistence.colbert_adapter,
        cache_port=infrastructure.cache_port,
        cognitive_boosters_enabled=getattr(
            settings, "RAG_COGNITIVE_BOOSTERS_ENABLED", True
        ),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/backend/test_cognitive_boosters_setting.py -q`
Expected: PASS (2 passed). If `test_rag_service_provider_wires_the_flag` cannot resolve the container in the test environment (missing infra), mark it `@pytest.mark.integration` and keep the settings-default test as the CI gate.

- [ ] **Step 5: Commit**

```bash
git add backend/api/animetix_project/settings.py backend/api/animetix/containers/agentic.py tests/backend/test_cognitive_boosters_setting.py
git commit -m "feat(rag): wire RAG_COGNITIVE_BOOSTERS_ENABLED setting (default on) into DI"
```

---

### Task 4: Ablation command + curated query fixture

**Files:**
- Create: `backend/api/animetix/management/commands/data/rag_ablation_queries.json`
- Create: `backend/api/animetix/management/commands/run_rag_ablation.py`
- Test: `tests/backend/test_run_rag_ablation.py`

**Interfaces:**
- Consumes: `rag.set_cognitive_boosters(bool)` (Task 1), `rag.generate_advanced_answer_with_context(...)` (Task 2), `RagasEvalService.evaluate_response(query, context, response) -> dict`, `GoldDatasetPort.get_all_entries()`.
- Produces: management command `run_rag_ablation` with `--source {curated,gold}` (default curated), `--media-type` (default Anime), `--limit` (default 0 = all).

- [ ] **Step 1: Create the curated fixture**

```json
// backend/api/animetix/management/commands/data/rag_ablation_queries.json
[
  {"query": "Un shonen avec un héros qui veut devenir le plus fort", "media_type": "Anime"},
  {"query": "Anime de mecha psychologique et déprimant", "media_type": "Anime"},
  {"query": "Tranche de vie réconfortante dans un café", "media_type": "Anime"},
  {"query": "Dark fantasy avec des chasseurs de démons", "media_type": "Anime"},
  {"query": "Romance lycéenne avec une tsundere", "media_type": "Anime"},
  {"query": "Thriller surnaturel avec des cahiers de la mort", "media_type": "Anime"},
  {"query": "Aventure de pirates à la recherche d'un trésor", "media_type": "Anime"},
  {"query": "Isekai où le héros est trop puissant", "media_type": "Anime"},
  {"query": "Sport intense autour du volley-ball", "media_type": "Anime"},
  {"query": "Science-fiction cyberpunk avec des cyborgs", "media_type": "Anime"},
  {"query": "Comédie absurde de magical girls", "media_type": "Anime"},
  {"query": "Seinen mature sur la guerre et la politique", "media_type": "Anime"},
  {"query": "Horreur psychologique en huis clos", "media_type": "Anime"},
  {"query": "Film Ghibli poétique sur la nature", "media_type": "Anime"},
  {"query": "Combats de pouvoirs surnaturels entre lycéens", "media_type": "Anime"}
]
```

- [ ] **Step 2: Write the failing test**

```python
# tests/backend/test_run_rag_ablation.py
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command


def _fake_container():
    rag = MagicMock()
    rag.generate_advanced_answer_with_context.return_value = ("ans", "ctx")
    judge = MagicMock()
    judge.evaluate_response.return_value = {
        "faithfulness": 0.8,
        "answer_relevancy": 0.8,
        "context_precision": 0.8,
    }
    container = MagicMock()
    container.agentic.rag_service.return_value = rag
    container.core.ragas_eval_service.return_value = judge
    return container, rag, judge


@patch("animetix.management.commands.run_rag_ablation.get_container")
def test_ablation_runs_pipeline_on_and_off(mock_gc):
    container, rag, _ = _fake_container()
    mock_gc.return_value = container
    out = StringIO()
    call_command("run_rag_ablation", "--source", "curated", "--limit", "1", stdout=out)

    modes = [c.args[0] for c in rag.set_cognitive_boosters.call_args_list]
    assert False in modes and True in modes  # both ablation arms run
    assert rag.generate_advanced_answer_with_context.call_count == 2  # ON + OFF
    assert "Verdict" in out.getvalue()


@patch("animetix.management.commands.run_rag_ablation.get_container")
def test_ablation_skips_failing_query(mock_gc):
    container, rag, _ = _fake_container()
    rag.generate_advanced_answer_with_context.side_effect = RuntimeError("pipeline down")
    mock_gc.return_value = container
    out = StringIO()
    call_command("run_rag_ablation", "--source", "curated", "--limit", "1", stdout=out)
    assert "skipped 1" in out.getvalue()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/backend/test_run_rag_ablation.py -q`
Expected: FAIL — `CommandError: Unknown command: 'run_rag_ablation'`.

- [ ] **Step 4: Write minimal implementation**

```python
# backend/api/animetix/management/commands/run_rag_ablation.py
import json
import logging
import os

from animetix.containers import get_container
from django.core.management.base import BaseCommand

logger = logging.getLogger("animetix.ablation")

METRICS = ["faithfulness", "answer_relevancy", "context_precision"]


class Command(BaseCommand):
    help = (
        "Ablation: run the RAG pipeline with cognitive boosters ON vs OFF and "
        "report RAGAS deltas (faithfulness / answer_relevancy / context_precision)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source", choices=["curated", "gold"], default="curated")
        parser.add_argument("--media-type", default="Anime")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **options):
        container = get_container()
        rag = container.agentic.rag_service()
        judge = container.core.ragas_eval_service()

        queries = self._load_queries(options["source"], options["media_type"], container)
        if options["limit"]:
            queries = queries[: options["limit"]]
        if not queries:
            self.stdout.write(self.style.WARNING("No queries to evaluate."))
            return

        agg = {"OFF": {}, "ON": {}}
        skipped = 0
        for item in queries:
            query = item["query"]
            media_type = item.get("media_type", options["media_type"])
            try:
                row = self._eval_both(rag, judge, query, media_type)
            except Exception as e:  # one bad query must not abort the run
                logger.warning(f"Skipped '{query}': {e}")
                skipped += 1
                continue
            for mode in ("OFF", "ON"):
                for metric, value in row[mode].items():
                    agg[mode].setdefault(metric, []).append(value)

        self._render(agg, len(queries), skipped)

    def _eval_both(self, rag, judge, query, media_type):
        result = {}
        for mode, enabled in (("OFF", False), ("ON", True)):
            rag.set_cognitive_boosters(enabled)
            answer, context = rag.generate_advanced_answer_with_context(query, media_type)
            result[mode] = judge.evaluate_response(query, context, answer)
        return result

    def _load_queries(self, source, media_type, container):
        if source == "gold":
            entries = container.persistence.gold_dataset_adapter().get_all_entries()
            return [
                {"query": e.get("question", ""), "media_type": media_type}
                for e in entries
                if e.get("question")
            ]
        path = os.path.join(os.path.dirname(__file__), "data", "rag_ablation_queries.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _render(self, agg, total, skipped):
        def mean(xs):
            return sum(xs) / len(xs) if xs else 0.0

        self.stdout.write(
            f"\nRAG cognitive-boosters ablation — "
            f"{total - skipped}/{total} queries (skipped {skipped})"
        )
        self.stdout.write(f"{'metric':<20}{'OFF':>10}{'ON':>10}{'delta':>14}")
        wins = 0
        for m in METRICS:
            off = mean(agg["OFF"].get(m, []))
            on = mean(agg["ON"].get(m, []))
            delta = on - off
            if delta > 0:
                wins += 1
            self.stdout.write(f"{m:<20}{off:>10.4f}{on:>10.4f}{delta:>+14.4f}")

        if wins >= 2:
            verdict = "ON improves on a majority of metrics"
        else:
            verdict = (
                "ON does NOT beat OFF on a majority of metrics "
                "-> boosters are demotion candidates"
            )
        self.stdout.write(self.style.NOTICE(f"\nVerdict: {verdict} ({wins}/3 improved)"))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/backend/test_run_rag_ablation.py -q`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add backend/api/animetix/management/commands/run_rag_ablation.py backend/api/animetix/management/commands/data/rag_ablation_queries.json tests/backend/test_run_rag_ablation.py
git commit -m "feat(rag): run_rag_ablation command — RAGAS A/B of cognitive boosters"
```

---

### Task 5: Documentation + verification sweep

**Files:**
- Modify: `docs/COMMANDS.md` (add the new command row)
- Verify: full affected suites + ruff

- [ ] **Step 1: Document the command**

Add a row under the management-commands table in `docs/COMMANDS.md`:

```markdown
| `python backend/api/manage.py run_rag_ablation --source curated` | Root | Runs the RAG pipeline with cognitive boosters ON vs OFF over a query set and reports RAGAS deltas (faithfulness / relevancy / context precision). Use `--source gold` for the Gold Dataset questions. Requires a live judge LLM. |
```

- [ ] **Step 2: Run the affected suites**

Run: `python -m pytest tests/core/test_advanced_rag_cognitive_toggle.py tests/core/test_advanced_rag_with_context.py tests/backend/test_cognitive_boosters_setting.py tests/backend/test_run_rag_ablation.py -q`
Expected: PASS (all).

- [ ] **Step 3: Lint**

Run: `python -m ruff check backend/core/domain/services/advanced_rag_service.py backend/api/animetix/management/commands/run_rag_ablation.py backend/api/animetix/containers/agentic.py`
Run: `python -m ruff format <same files + the 4 test files>`
Expected: All checks passed; format clean.

- [ ] **Step 4: Commit**

```bash
git add docs/COMMANDS.md
git commit -m "docs: document run_rag_ablation command"
```

---

## Notes for the executor

- Do **not** flip the production default to OFF — that is an evidence-gated follow-up the user runs after using this harness.
- The real ablation run (`run_rag_ablation` against a live judge LLM + populated catalog) is a user task; the tests here mock all LLM I/O and assert wiring/aggregation only.
