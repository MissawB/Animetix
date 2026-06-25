# finetuning_dataset Orchestrator Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add meaningful, case-by-case tests that actually invoke `run_generate_instruction_dataset()` (heavy deps mocked, tiny fixtures), covering section assembly, tier-variation counts, Gemini client-init gating, the augmentation path, and the noise-rate fallback.

**Architecture:** Test-only. A shared context-manager helper (`_orchestrator_env`) patches the module's heavy surface (generator helpers, `load_dataset`, `genai`, `paraphrase_text_via_gemini`, the DB/OUTPUT path constants, `save_paraphrase_cache`) and the `SystemRandom` shadow (`fd.random`) onto a seeded `Random`, writes tiny temp fixture DBs, then each test calls the orchestrator and asserts on the written JSONL. These are characterization tests of existing behavior — they PASS on first run.

**Tech Stack:** Python, `unittest`, `unittest.mock`, `tempfile`. No network, no GPU.

**Spec:** [docs/specs/2026-06-25-finetuning-dataset-orchestrator-tests-design.md](../specs/2026-06-25-finetuning-dataset-orchestrator-tests-design.md)

## Global Constraints

- **Test-only.** No changes to `backend/pipeline/mlops/finetuning_dataset.py` or any production file.
- All new code goes in `tests/mlops/test_finetuning_dataset.py` (append; match the existing `unittest.TestCase` style).
- **`fd.random` MUST be patched** to a seedable `random.Random(seed)` in every test (line 14 shadows `random` with `SystemRandom`, so `seed()` alone is a no-op).
- These are **characterization** tests: each runs against existing production code and is **Expected: PASS** on first run. A failure means the TEST is wrong (fix the test) — unless it reveals a genuine production bug, in which case STOP and report it (the spec forbids production changes).
- Patch every mocked name on the module object `fd` (the orchestrator calls them as bare module-level names): `import backend.pipeline.mlops.finetuning_dataset as fd`.
- Assertions target the orchestrator's own logic (section assembly, tier counts, client gating, env fallback) — never the mocked helpers' return values, exact instruction strings, or shuffle order.
- Run commands from the worktree root: `C:\Users\bahma\PycharmProjects\Projet solo\Double_scenario_Project\.claude\worktrees\test-finetuning-dataset-coverage`. Tests run with `python -m pytest`.

---

### Task 1: Shared fixture helper + integration happy-path test

**Files:**
- Modify (append): `tests/mlops/test_finetuning_dataset.py`

**Interfaces:**
- Consumes: `backend.pipeline.mlops.finetuning_dataset` (module under test).
- Produces (used by Tasks 2–4):
  - `_items(tag: str, n: int) -> list[dict]` — n tagged instruction dicts (`instruction=f"{tag}-{i}"`).
  - `_orchestrator_env(tmpdir, *, animes=None, mangas=None, chars=None, env=None, genai_mock=None, paraphrase_mock=None, seed=0)` — context manager yielding the output JSONL path; patches the whole heavy surface. `None` DB → a non-existent path (so `os.path.exists` is False); `[]` → an empty-list fixture file.
  - `class TestRunGenerateInstructionDataset(unittest.TestCase)` with helper method `_read(path) -> list[dict]`.

- [ ] **Step 1: Append the helper and the integration test**

Append to `tests/mlops/test_finetuning_dataset.py` (the file already imports `os`, `sys`, `unittest`, and `MagicMock, patch`; add the new imports at the top of the file if not present: `import contextlib`, `import json`, `import random as _py_random`, `import tempfile`, and `import backend.pipeline.mlops.finetuning_dataset as fd`):

```python
# --- Orchestrator integration tests (run_generate_instruction_dataset) --------

_SIMPLE_GENERATORS = (
    "generate_transmedia_instructions",
    "generate_awards_and_magazines_instructions",
    "generate_songs_and_seiyuu_instructions",
    "generate_french_market_relations_instructions",
    "generate_japanese_market_relations_instructions",
    "generate_french_market_profile_instructions",
    "generate_japanese_market_profile_instructions",
    "generate_volumes_and_episodes_instructions",
    "generate_mcp_tool_instructions",
)


def _items(tag, n):
    """n tagged instruction dicts, each with a unique instruction so dedup keeps them."""
    return [
        {"instruction": f"{tag}-{i}", "input": "", "output": "o", "language": "Français"}
        for i in range(n)
    ]


@contextlib.contextmanager
def _orchestrator_env(
    tmpdir,
    *,
    animes=None,
    mangas=None,
    chars=None,
    env=None,
    genai_mock=None,
    paraphrase_mock=None,
    seed=0,
):
    """Patch the heavy surface of run_generate_instruction_dataset and yield the output path.

    DB args: a list writes a temp JSON fixture; None points the constant at a
    non-existent path so the os.path.exists guard is False.
    """

    def _write(name, data):
        if data is None:
            return os.path.join(tmpdir, name + "_missing.json")
        path = os.path.join(tmpdir, name + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    anime_db = _write("anime", animes)
    manga_db = _write("manga", mangas)
    char_db = _write("char", chars)
    out_path = os.path.join(tmpdir, "out.jsonl")

    def _fake_load_dataset(path, split=None, **kwargs):
        lang = "fr" if "alpaca-cleaned-fr" in path else "en"
        return [
            {"instruction": f"general-{lang}", "input": "", "output": "o"}
            for _ in range(50)
        ]

    def _fixed(value):
        return MagicMock(side_effect=lambda *a, **k: value)

    with contextlib.ExitStack() as stack:

        def patch_attr(name, new):
            stack.enter_context(patch.object(fd, name, new))

        patch_attr("ANIME_DB", anime_db)
        patch_attr("MANGA_DB", manga_db)
        patch_attr("CHAR_DB", char_db)
        patch_attr("OUTPUT_DATASET", out_path)
        patch_attr("random", _py_random.Random(seed))
        patch_attr("load_dataset", MagicMock(side_effect=_fake_load_dataset))
        patch_attr("save_paraphrase_cache", MagicMock())

        for gen in _SIMPLE_GENERATORS:
            patch_attr(gen, MagicMock(side_effect=lambda *a, _g=gen, **k: _items(_g, 2)))
        patch_attr("generate_rag_context_instructions", _fixed(_items("rag", 2)))
        patch_attr("generate_otaku_meta_instructions", _fixed(_items("meta", 3)))
        patch_attr(
            "generate_negative_refusal_examples", _fixed(_items("refusal", 2))
        )
        patch_attr(
            "generate_multiturn_dialogues",
            _fixed(
                [
                    {"turns": [{"user": "u", "assistant": "a"}], "language": "Français"},
                    {"turns": [{"user": "u2", "assistant": "a2"}], "language": "English"},
                ]
            ),
        )
        if genai_mock is not None:
            patch_attr("genai", genai_mock)
        if paraphrase_mock is not None:
            patch_attr("paraphrase_text_via_gemini", paraphrase_mock)
        if env is not None:
            stack.enter_context(patch.dict(os.environ, env, clear=False))

        yield out_path


class TestRunGenerateInstructionDataset(unittest.TestCase):
    def _read(self, path):
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    def test_integration_happy_path_assembles_all_sections(self):
        animes = [
            {  # idx 0 -> French branch; Tier-1 (>150k) -> 5 variations
                "title": "TestAnimeAlpha",
                "genres": ["Action"],
                "studios": ["S"],
                "tags": ["t"],
                "popularity": 200000,
                "year": 2020,
            },
            {  # idx 1 -> English branch; Tier-3 (<=50k) -> 1 variation
                "title": "TestAnimeBeta",
                "genres": ["Comedy"],
                "studios": ["S"],
                "tags": ["t"],
                "popularity": 1000,
                "year": 2020,
            },
        ]
        mangas = [
            {
                "title": "TestMangaA",
                "genres": ["Action"],
                "tags": ["t"],
                "popularity": 1000,
                "year": 2020,
            }
        ]
        chars = [
            {  # origin deliberately NOT one of the anime titles, to avoid contaminating the counts
                "name": "TestCharA",
                "origin": "TestCharOrigin",
                "entities": {"organizations": ["Org"]},
                "popularity": {"favourites": 100, "rank": 10},
                "metadata": {"height": "170cm"},
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=mangas,
                chars=chars,
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                },
            ) as out:
                fd.run_generate_instruction_dataset()
                data = self._read(out)

        self.assertTrue(data, "orchestrator wrote an empty dataset")

        def instr(item):
            return item.get("instruction", "")

        # Every section is wired into the final dataset.
        self.assertTrue(any(instr(it).startswith("transmedia") for it in data))
        self.assertTrue(any(instr(it).startswith("rag") for it in data))
        self.assertTrue(any(instr(it).startswith("meta") for it in data))
        self.assertTrue(any(instr(it).startswith("refusal") for it in data))
        self.assertTrue(any(instr(it) in ("general-fr", "general-en") for it in data))
        self.assertTrue(any("turns" in it for it in data))

        # Tier-variation counts (augmentation off, noise off -> instructions pristine).
        alpha = [it for it in data if "TestAnimeAlpha" in instr(it)]
        beta = [it for it in data if "TestAnimeBeta" in instr(it)]
        self.assertEqual(len(alpha), 5, "Tier-1 anime should yield 5 variations")
        self.assertEqual(len(beta), 1, "Tier-3 anime should yield 1 variation")
```

- [ ] **Step 2: Run the integration test — expect PASS**

Run: `python -m pytest tests/mlops/test_finetuning_dataset.py::TestRunGenerateInstructionDataset::test_integration_happy_path_assembles_all_sections -q`
Expected: PASS (1 passed). If it FAILS, the test is wrong — debug the fixture/mocks; do NOT modify production code. (If the failure reveals a genuine bug in `run_generate_instruction_dataset`, STOP and report it.)

- [ ] **Step 3: Commit**

```bash
git add tests/mlops/test_finetuning_dataset.py
git commit -m "test(mlops): integration test for run_generate_instruction_dataset section assembly + tier counts"
```

---

### Task 2: Client-init gating tests

**Files:**
- Modify (append): `tests/mlops/test_finetuning_dataset.py`

**Interfaces:**
- Consumes: `_orchestrator_env`, `TestRunGenerateInstructionDataset` (Task 1).

- [ ] **Step 1: Append two methods to `TestRunGenerateInstructionDataset`**

```python
    def test_client_initialized_when_augmentation_enabled(self):
        genai_mock = MagicMock()
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=[],
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "true",
                    "GEMINI_API_KEY": "k",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                },
                genai_mock=genai_mock,
            ):
                fd.run_generate_instruction_dataset()
        genai_mock.Client.assert_called_once_with(api_key="k")

    def test_client_not_initialized_when_augmentation_disabled(self):
        genai_mock = MagicMock()
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=[],
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "GEMINI_API_KEY": "k",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                },
                genai_mock=genai_mock,
            ):
                fd.run_generate_instruction_dataset()
        genai_mock.Client.assert_not_called()
```

- [ ] **Step 2: Run both tests — expect PASS**

Run: `python -m pytest "tests/mlops/test_finetuning_dataset.py::TestRunGenerateInstructionDataset::test_client_initialized_when_augmentation_enabled" "tests/mlops/test_finetuning_dataset.py::TestRunGenerateInstructionDataset::test_client_not_initialized_when_augmentation_disabled" -q`
Expected: PASS (2 passed).

- [ ] **Step 3: Commit**

```bash
git add tests/mlops/test_finetuning_dataset.py
git commit -m "test(mlops): cover Gemini client-init gating in run_generate_instruction_dataset"
```

---

### Task 3: Augmentation path test

**Files:**
- Modify (append): `tests/mlops/test_finetuning_dataset.py`

**Interfaces:**
- Consumes: `_orchestrator_env`, `TestRunGenerateInstructionDataset` (Task 1).

- [ ] **Step 1: Append a method to `TestRunGenerateInstructionDataset`**

```python
    def test_augmentation_calls_paraphrase_for_tier1_title(self):
        genai_mock = MagicMock()
        paraphrase_mock = MagicMock(return_value="paraphrased")
        animes = [
            {  # Tier-1 (>150k) -> enters the augmented set -> 5 paraphrase calls
                "title": "AugAnime",
                "genres": ["Action"],
                "studios": ["S"],
                "tags": ["t"],
                "popularity": 200000,
                "year": 2020,
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "true",
                    "GEMINI_API_KEY": "k",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                },
                genai_mock=genai_mock,
                paraphrase_mock=paraphrase_mock,
            ):
                fd.run_generate_instruction_dataset()
        # One Tier-1 anime in the augmented set triggers the 5-variation paraphrase branch.
        self.assertEqual(paraphrase_mock.call_count, 5)
```

- [ ] **Step 2: Run the test — expect PASS**

Run: `python -m pytest "tests/mlops/test_finetuning_dataset.py::TestRunGenerateInstructionDataset::test_augmentation_calls_paraphrase_for_tier1_title" -q`
Expected: PASS (1 passed). If `call_count` differs, read lines 458–516 of `finetuning_dataset.py` to reconcile the expected count — the test must match the real branch, not the other way round.

- [ ] **Step 3: Commit**

```bash
git add tests/mlops/test_finetuning_dataset.py
git commit -m "test(mlops): cover Gemini augmentation paraphrase branch for Tier-1 titles"
```

---

### Task 4: Noise-rate fallback test + coverage confirmation

**Files:**
- Modify (append): `tests/mlops/test_finetuning_dataset.py`

**Interfaces:**
- Consumes: `_orchestrator_env`, `TestRunGenerateInstructionDataset` (Task 1).

- [ ] **Step 1: Append a method to `TestRunGenerateInstructionDataset`**

```python
    def test_invalid_noise_rate_falls_back_without_error(self):
        animes = [
            {
                "title": "NoiseAnime",
                "genres": ["Action"],
                "studios": ["S"],
                "tags": ["t"],
                "popularity": 1000,
                "year": 2020,
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "not-a-number",
                },
            ) as out:
                # Invalid rate -> ValueError caught -> 0.12 fallback; must not raise.
                fd.run_generate_instruction_dataset()
                data = self._read(out)
        self.assertTrue(data, "orchestrator should still produce a dataset on noise-rate fallback")
```

- [ ] **Step 2: Run the test — expect PASS**

Run: `python -m pytest "tests/mlops/test_finetuning_dataset.py::TestRunGenerateInstructionDataset::test_invalid_noise_rate_falls_back_without_error" -q`
Expected: PASS (1 passed).

- [ ] **Step 3: Run the whole file + confirm coverage rose meaningfully**

Run: `python -m pytest tests/mlops/test_finetuning_dataset.py -q --cov=backend.pipeline.mlops.finetuning_dataset --cov-report=term-missing`
Expected: all tests PASS (the original 20 + 5 new). The coverage line for `finetuning_dataset.py` should rise from 14% to well above (the `209-1415` body is now largely exercised). The `FAIL Required test coverage of 75.0%` line, if present, is a `--cov-fail-under` artifact of scoping `--cov` to a single module — it is NOT a test failure; ignore it (confirm the test count line reads `25 passed`).

- [ ] **Step 4: Commit**

```bash
git add tests/mlops/test_finetuning_dataset.py
git commit -m "test(mlops): cover noise-rate env fallback in run_generate_instruction_dataset"
```

---

## Self-Review

**Spec coverage:**
- Integration happy-path (sections + tier counts, aug OFF, deps mocked, fixtures, patched `random`) → Task 1. ✓
- Tier-variation counts → folded into Task 1 (5/1 assertions), per spec note. ✓
- Client-init gating (on/off) → Task 2. ✓
- Augmentation path (paraphrase invoked for Tier-1) → Task 3. ✓
- Noise-rate env fallback → Task 4. ✓
- `SystemRandom` shadow handled (`fd.random` patched in `_orchestrator_env`) → all tasks. ✓
- Test-only, CI-safe (no network/GPU), determinism → Global Constraints + helper. ✓

**Placeholder scan:** none — every test and the helper are shown in full; commands and expected results are literal.

**Type/name consistency:** `_orchestrator_env(tmpdir, *, animes, mangas, chars, env, genai_mock, paraphrase_mock, seed)` and `_items(tag, n)` are defined in Task 1 and consumed with matching kwargs in Tasks 2–4. Patch targets (`generate_*`, `load_dataset`, `genai`, `paraphrase_text_via_gemini`, `ANIME_DB`/`MANGA_DB`/`CHAR_DB`/`OUTPUT_DATASET`, `save_paraphrase_cache`, `random`) all match the names imported into `finetuning_dataset`. Tier mapping (T1>150k→5, T3≤50k→1) matches the source loop.
