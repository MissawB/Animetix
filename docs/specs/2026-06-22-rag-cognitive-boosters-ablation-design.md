# Design — RAG cognitive boosters: toggle + ablation harness

**Date:** 2026-06-22
**Status:** Approved (approach A)
**TODO source:** "Archi IA — boosters « cognitifs » dans le chemin RAG de prod sans preuve de gain"

## Problem

`AdvancedRAGService` wires two experimental "cognitive boosters" — `QuantumCognitiveService`
(non-commutative Born-rule preference) and the neuromorphic stack (`SynapticPlasticityService`
+ `LiquidNeuralNetworkService`) — directly into the **production** retrieval/reranking path.
`_adjust_scores_cognitively` rescales every candidate as
`final_score = base_score · (1 + α·cog_multiplier)` and runs on both `hybrid_search` and
`rerank_results`. There is **no evidence** these boosters improve answer quality, and they add
maintenance + GPU surface to a solo project.

We cannot resolve "keep vs demote" by code review — it requires measurement (RAGAS over a live
judge LLM + dataset). This work delivers the **toggle** and the **measurement harness** so the
decision becomes data-driven. It does **not** change the production default (boosters stay ON)
and does **not** make the keep/demote decision.

## Current state (verified)

- A disable path already exists but only via DI constructor sentinels: passing
  `quantum_model=None, plasticity_simulator=None` makes `_get_cognitive_models` return
  `(None, None, None)`, after which `_adjust_scores_cognitively` returns candidates unchanged.
  There is no config flag and no runtime switch.
- `RagasEvalService.evaluate_response(query, context, response)` is an LLM-as-judge returning
  `faithfulness / answer_relevancy / context_precision`. `run_batch_evaluation()` judges
  *pre-generated* answers from a Gold Dataset — it does **not** re-run the pipeline, so it cannot
  by itself ablate the boosters (which change retrieval → context → answer).
- `generate_advanced_answer` returns only the answer text (no context), so RAGAS cannot be fed
  directly from it today.
- Management-command precedent exists: `run_data_quality_tests`, `run_red_teaming`.

## Goals / non-goals

**Goals**
1. A single, reliable on/off control for the cognitive boosters (config default + runtime switch).
2. An in-process ablation harness that re-runs the RAG pipeline ON vs OFF per query, judges each
   with RAGAS, and reports the per-metric delta.
3. All new behavior covered by tests that run in CI (no live LLM dependency).

**Non-goals**
- Deciding to keep or remove the boosters (needs a live run by the user).
- Changing the production default (stays ON).
- Touching the boosters' internal math or the Ghost Labs demos.

## Design

### 1. Toggle — single control point

- `AdvancedRAGService.__init__` gains `cognitive_boosters_enabled: bool = True`
  (default preserves current behavior). Stored as `self.cognitive_boosters_enabled`.
- `_get_cognitive_models` returns `(None, None, None)` immediately when the flag is False —
  the **single** chokepoint, so ablation is guaranteed on every consumer (`hybrid_search`,
  `rerank_results`, `update_cognitive_state`). The existing `None`-sentinel disable path is kept.
- `set_cognitive_boosters(enabled: bool)` lets the harness flip the flag at runtime, in-process.
- The service itself stays framework-free (just the bool param). The DI container sets the
  production default by passing `cognitive_boosters_enabled=getattr(settings,
  "RAG_COGNITIVE_BOOSTERS_ENABLED", True)` to the `AdvancedRAGService` provider — so the default
  is `True` (prod unchanged) and can be flipped later from settings without touching the service.

### 2. Expose context for RAGAS

- Extract `generate_advanced_answer_with_context(query, media_type, user_id=None) -> tuple[str, str]`
  returning `(answer, context)`.
- `generate_advanced_answer` becomes a thin wrapper returning only the answer — **public
  signature and behavior unchanged** (no regression for existing callers).

### 3. Ablation harness — `run_rag_ablation` management command

Location: `backend/api/animetix/management/commands/run_rag_ablation.py`.

- Args: `--source {curated,gold}` (default `curated`), `--media-type` (default `Anime`),
  `--limit` (cap query count).
- `curated` source: versioned fixture
  `backend/api/animetix/management/commands/data/rag_ablation_queries.json` (~15–20
  representative anime queries: `[{"query": "...", "media_type": "Anime"}, ...]`).
- `gold` source: pull questions via `GoldDatasetPort.get_all_entries()` (re-generate answers
  through the pipeline; the gold pre-baked answers are ignored).
- Per query: resolve the `AdvancedRAGService` from the container; run OFF then ON using
  `set_cognitive_boosters(False/True)` + `generate_advanced_answer_with_context`; judge each
  `(query, context, answer)` with `RagasEvalService.evaluate_response`; accumulate.
- Output: a table **OFF / ON / Δ** for faithfulness, answer_relevancy, context_precision, plus a
  one-line verdict (e.g. "ON does not beat OFF on N/3 metrics → boosters are demotion
  candidates"). Optional persistence via `eval_port`.

### 4. Data flow

```
query ──▶ AdvancedRAGService (boosters OFF) ──▶ (answer_off, context_off) ──▶ RagasEval ─┐
      └─▶ AdvancedRAGService (boosters ON)  ──▶ (answer_on,  context_on)  ──▶ RagasEval ─┴─▶ aggregate Δ ─▶ table + verdict
```

### 5. Error handling

- A query that throws (pipeline or judge) is logged and skipped; the run continues and the
  skipped count is reported (never abort the whole ablation on one failure).
- Missing/empty gold dataset with `--source gold`: clear message, exit without crashing.
- Empty curated fixture: clear message.

## Testing (TDD)

- `_get_cognitive_models` / `_adjust_scores_cognitively`: disabled flag → scores unchanged
  (no-op); enabled → boost applied. Flip via `set_cognitive_boosters`.
- `generate_advanced_answer_with_context`: returns the same context string that
  `generate_advanced_answer` builds (LLM mocked), and `generate_advanced_answer` still returns
  only the answer.
- `run_rag_ablation`: with a mocked inference engine + mocked `RagasEvalService`, asserts the
  command runs each query twice (ON and OFF), aggregates correctly, and renders the delta table;
  curated and gold sources both exercised; one failing query is skipped without aborting.
- No test depends on a live LLM (all mocked) → CI-safe.

## Risks / mitigations

- **Risk:** the runtime flag desyncs cached cognitive state per user. *Mitigation:* the flag only
  gates `_get_cognitive_models`; cache keys are unchanged, OFF simply skips load/use.
- **Risk:** harness results are noisy with a tiny query set. *Mitigation:* curated set ~15–20;
  verdict wording is advisory, not a hard gate; the user runs it against their real judge LLM.

## Out of scope / follow-up

- Running the ablation and acting on the verdict (user task, needs live judge + data).
- Flipping the prod default to OFF (separate, evidence-gated change).
