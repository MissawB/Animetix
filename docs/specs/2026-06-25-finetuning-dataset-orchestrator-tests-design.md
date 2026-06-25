# Design — Tests for `run_generate_instruction_dataset` orchestrator

**Date:** 2026-06-25
**Status:** Approved
**TODO source:** "Couverture backend — orchestrateur `finetuning_dataset` : `run_generate_instruction_dataset` (433 lignes, 14 %). À traiter au cas par cas, sans gonfler la couverture." ([TODO.md](../../TODO.md))

## Problem

`backend/pipeline/mlops/finetuning_dataset.py::run_generate_instruction_dataset()` is a 433-line
orchestrator at 14 % coverage. The existing `tests/mlops/test_finetuning_dataset.py` thoroughly
covers the **helper** functions (generators, cleaning, paraphrase, dedup, ratios) but **never calls
the orchestrator itself**: the three `test_run_generate_*` tests only inspect `OUTPUT_DATASET` *if it
already exists* (`if os.path.exists(OUTPUT_DATASET)`), which is false in CI, so they are no-ops. The
uncovered span is lines 209–1415 (the whole body).

Per the TODO, the goal is **meaningful, case-by-case tests — not coverage padding**. Coverage rising
is a byproduct of real assertions, not the target.

## Goals / non-goals

**Goals**
- Actually invoke `run_generate_instruction_dataset()` end-to-end with heavy dependencies mocked and
  tiny fixtures, asserting real orchestration behavior.
- Cover the genuinely branchy logic: tiered variation counts, Gemini client-init gating, the
  augmentation path, and the noise-rate env fallback.

**Non-goals**
- No production changes (test-only).
- No assertions on shuffle order or on every f-string instruction variant.
- No re-testing helpers already covered (generators, dedup, ratios, paraphrase, noise injection).
- Not chasing a coverage percentage target.

## Key constraints (discovered while reading the code)

- **`random` is `SystemRandom`** (module line 14: `random = random.SystemRandom()`), so
  `random.seed()` does **nothing**. For any deterministic assertion, tests must patch the module
  attribute `finetuning_dataset.random` with a seedable `random.Random(<seed>)` instance.
- The orchestrator reads DB files via the module-level path constants `ANIME_DB`/`MANGA_DB`/`CHAR_DB`
  and guards each read with `os.path.exists`. Tests point these constants at temp fixture files.
- Output is written to the module constant `OUTPUT_DATASET` (JSONL) and `save_paraphrase_cache()` is
  called at the end. Tests patch `OUTPUT_DATASET` to a temp path and patch/neutralize
  `save_paraphrase_cache`.
- Augmentation requires ALL of: `ANIMETIX_AUGMENT_DATA` truthy, `GEMINI_API_KEY` set, `genai` import
  available, AND the item's title/name in the popularity-derived `augmented_*` set (built only when a
  client exists). Tests control these explicitly.

## Test design (all in `tests/mlops/test_finetuning_dataset.py`, matching the existing `unittest` style)

### 1. Integration happy-path (augmentation OFF)
Drive the whole function with:
- The ~13 generator helpers patched to return small, tagged lists (so each section is identifiable
  and the body runs fast): transmedia, awards/magazines, songs/seiyuu, FR/JP market relations, FR/JP
  market profiles, volumes/episodes, MCP, RAG, multiturn dialogues, refusals, otaku-meta.
- `ANIME_DB`/`MANGA_DB`/`CHAR_DB` patched to temp JSON fixtures: at least one Tier-1 anime
  (`popularity > 150000`) and one Tier-3 anime (`<= 50000`); analogous tiny manga + one character.
- `load_dataset` patched (general instructions); `OUTPUT_DATASET` patched to a temp file;
  `save_paraphrase_cache` patched to a no-op; `ANIMETIX_AUGMENT_DATA` unset/false so the client is
  `None`.
- `finetuning_dataset.random` patched to `random.Random(0)` for determinism.

Assertions:
- The output file exists and every line parses as JSON.
- Entries from each mocked section appear in the output (specialized + meta + general + multiturn +
  refusal), identified by their tag.
- The Tier-1 anime produces **5** specialized variations and the Tier-3 anime produces **1**
  (tier-count logic), checked by counting output entries whose `instruction` references each title.
- The function returns without error.

### 2. Tier-variation counts (focused)
A narrower variant (or sub-assertions of test 1) confirming the anime tier mapping
(T1>150k→5, 50k<T2≤150k→3, T3≤50k→1). May reuse the same fixtures with augmentation OFF so the
5/3/1 counts come purely from the static-template branch (`p1 = … = profile`).

### 3. Client-init gating
- With `ANIMETIX_AUGMENT_DATA=true`, `GEMINI_API_KEY=x`, and `finetuning_dataset.genai` patched to a
  mock: assert `genai.Client(api_key="x")` is constructed.
- With augmentation off or key missing: assert the client is never constructed (stays `None`), via a
  patched `genai` whose `Client` is asserted `not_called`.

### 4. Augmentation path
With a mock client wired (augmentation ON) and a fixture anime whose title lands in the >150k tier,
patch `paraphrase_text_via_gemini` and assert it is invoked for that title (the
`if client and title in augmented_anime_titles` branch), confirming the 5 paraphrase calls fire for a
Tier-1 item.

### 5. Noise-rate env fallback
Set `ANIMETIX_QUERY_NOISE_RATE` to an invalid value (e.g. `"abc"` or `"2.0"`) and assert the function
completes without raising (the `except ValueError` → 0.12 fallback path), with augmentation OFF and
minimal fixtures.

## Testing strategy notes

- Use `unittest.mock.patch` / `patch.dict(os.environ, …)` and `tempfile` for fixtures and output,
  matching the file's existing conventions (it already patches `load_dataset` and uses
  `patch.dict(os.environ, …)`).
- Keep generator mocks tiny (1–3 items each) so the suite stays fast and assertions stay legible.
- Each test cleans up temp files (or uses `tempfile.TemporaryDirectory`).
- These are CI-safe: no network (`load_dataset`/`genai` mocked), no real GPU, deterministic via the
  patched `Random`.

## Risks / mitigations

- **Risk:** forgetting the `SystemRandom` shadow makes a test flaky. *Mitigation:* every test asserting
  on counts/selection patches `finetuning_dataset.random`; tests that don't assert on randomness
  don't need it but the integration test does (it samples meta + shuffles + injects noise).
- **Risk:** over-mocking turns the test into a tautology. *Mitigation:* assertions target the
  orchestrator's own logic (tier counts, section assembly, client gating, env fallback), not the
  return values of the mocked helpers.
- **Risk:** brittle assertions on exact output strings. *Mitigation:* assert on structure/section
  presence/counts, not on full instruction text.

## Out of scope / follow-up

- Refactoring the orchestrator into smaller testable units (a larger, separate effort).
- Asserting exact shuffle/sample ordering.
