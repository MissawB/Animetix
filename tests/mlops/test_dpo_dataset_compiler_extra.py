# -*- coding: utf-8 -*-
"""
Additional coverage tests for backend.pipeline.mlops.dpo_dataset_compiler.

Targets error/edge/fallback branches that the base test suite leaves uncovered:
cache load/save error handling, Gemini client init, corruption fallbacks,
LLM critic retry/exception paths, and compile_dpo_pairs branch handling.

All external I/O (LLM calls, file/DB) is mocked; tests assert real behavior.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import backend.pipeline.mlops.dpo_dataset_compiler as compiler


class TestCacheErrorHandling(unittest.TestCase):
    def test_init_dpo_cache_corrupt_file_resets_to_empty(self):
        """Lines 111-113: a corrupt cache JSON file must be caught and reset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "gemini_dpo_cache.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write("{ this is : not valid json ]")
            # Seed with stale data to prove it is wiped
            compiler.DPO_CACHE = {"stale": "value"}
            compiler.init_dpo_cache(tmpdir)
            self.assertEqual(compiler.DPO_CACHE, {})

    def test_save_dpo_cache_handles_write_error(self):
        """Lines 125-126: save errors are swallowed (logged), not raised."""
        with tempfile.TemporaryDirectory() as tmpdir:
            compiler.init_dpo_cache(tmpdir)
            compiler.DPO_CACHE = {"k": "v"}
            with patch(
                "backend.pipeline.mlops.dpo_dataset_compiler.open",
                side_effect=OSError("disk full"),
            ):
                # Must not raise
                compiler.save_dpo_cache()

    def test_save_dpo_cache_noop_without_file(self):
        """Early return when DPO_CACHE_FILE is unset."""
        original = compiler.DPO_CACHE_FILE
        try:
            compiler.DPO_CACHE_FILE = None
            # Should simply return without error
            compiler.save_dpo_cache()
        finally:
            compiler.DPO_CACHE_FILE = original


class TestInitGeminiClient(unittest.TestCase):
    def tearDown(self):
        compiler.GEMINI_CLIENT = None

    def test_init_gemini_client_no_api_key(self):
        """Lines 155-159: no API key => client stays None."""
        compiler.GEMINI_CLIENT = MagicMock()  # prove it gets reset to None
        # init_gemini_client imports load_dotenv function-locally
        # (`from dotenv import load_dotenv`), so we patch the real source
        # `dotenv.load_dotenv` — patching a module-level name would miss it and
        # the real load_dotenv would read a developer's local .env, leaking
        # GEMINI_API_KEY into this "no key" case. Hermetic with or without .env.
        with (
            patch("dotenv.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
        ):
            compiler.init_gemini_client()
        self.assertIsNone(compiler.GEMINI_CLIENT)

    def test_init_gemini_client_with_key_success(self):
        """Lines 148-151: API key + genai present => client built."""
        fake_client = MagicMock()
        fake_genai = MagicMock()
        fake_genai.Client.return_value = fake_client
        with (
            patch("dotenv.load_dotenv"),
            patch.dict(os.environ, {"GEMINI_API_KEY": "abc123"}, clear=True),
            patch.object(compiler, "genai", fake_genai),
        ):
            compiler.init_gemini_client()
        self.assertIs(compiler.GEMINI_CLIENT, fake_client)
        fake_genai.Client.assert_called_once_with(api_key="abc123")

    def test_init_gemini_client_with_key_failure(self):
        """Lines 152-154: client construction raising => GEMINI_CLIENT None."""
        fake_genai = MagicMock()
        fake_genai.Client.side_effect = RuntimeError("boom")
        with (
            patch("dotenv.load_dotenv"),
            patch.dict(os.environ, {"GEMINI_API_KEY": "abc123"}, clear=True),
            patch.object(compiler, "genai", fake_genai),
        ):
            compiler.init_gemini_client()
        self.assertIsNone(compiler.GEMINI_CLIENT)


class TestCorruptFactSubstitutionFallbacks(unittest.TestCase):
    def test_number_fallback_when_no_entities(self):
        """Lines 682-689: no year/entity => corrupt a plain number."""
        random_seq = compiler.random
        random_seq.seed(7)
        text = "Il a vendu 12 volumes au total."
        out = compiler.corrupt_fact_substitution(text, "Français")
        self.assertNotEqual(out, text)
        # The literal "12" should have been replaced by a different number
        self.assertNotIn(" 12 ", f" {out} ")

    def test_word_swap_ultimate_fallback(self):
        """Lines 693-698: no numbers/entities => swap two long words."""
        compiler.random.seed(3)
        text = "alpha bravo charlie delta echo foxtrot"
        out = compiler.corrupt_fact_substitution(text, "Français")
        self.assertNotEqual(out, text)
        # Same multiset of words, only order changed
        self.assertEqual(sorted(out.split()), sorted(text.split()))

    def test_no_change_possible_returns_original(self):
        """All fallbacks fail (no number, <2 long words) => text unchanged."""
        text = "a b c"  # no years, no entities, no numbers, no long words
        out = compiler.corrupt_fact_substitution(text, "Français")
        self.assertEqual(out, text)

    def test_related_map_empty_choices_branch(self):
        """Line 658: entity present but RELATED_ENTITIES_MAP empty -> fallback list."""
        # Pick a studio guaranteed to be in STUDIOS_LIST
        studio = compiler.STUDIOS_LIST[0]
        text = f"Ce projet a été produit par {studio} en grande pompe."
        with patch.object(compiler, "RELATED_ENTITIES_MAP", {}):
            compiler.random.seed(1)
            out = compiler.corrupt_fact_substitution(text, "Français")
        self.assertNotEqual(out, text)


class TestCorruptTonalDeviationBranches(unittest.TestCase):
    def test_english_code_switching(self):
        """Lines 754-768: English code-switching branch."""
        text = "This masterpiece has great characters and amazing animation."
        with patch.object(compiler.random, "choice", side_effect=lambda seq: seq[0]):
            out = compiler.corrupt_tonal_deviation(text, "English")
        # English swaps and prepender/appender applied
        self.assertTrue(out.startswith("So, basically,"))
        self.assertIn("sakuga", out)  # animation -> sakuga
        self.assertIn("chara", out)  # characters -> chara

    def test_redundancy_single_sentence_branch(self):
        """Lines 787-788: redundancy with a single sentence uses prepend/append."""
        text = "Un texte sans ponctuation de fin de phrase multiple"

        def fake_choice(seq):
            return seq[0]

        with (patch.object(compiler.random, "choice", side_effect=fake_choice),):
            # Force the "redundancy" strategy. random.choice is also used to
            # select the strategy first, so return the matching element.
            with patch.object(
                compiler.random,
                "choice",
                side_effect=lambda seq: (
                    "redundancy"
                    if seq == ["code_switching", "redundancy", "condescending"]
                    else seq[0]
                ),
            ):
                out = compiler.corrupt_tonal_deviation(text, "Français")
        self.assertTrue(out.startswith("Pour ce qui est de ce sujet"))

    def test_condescending_with_comma_branch(self):
        """Lines 808-809: condescending branch when text contains a comma."""
        text = "Cet anime, produit par MAPPA, est excellent et bien réalisé."
        with patch.object(
            compiler.random,
            "choice",
            side_effect=lambda seq: (
                "condescending"
                if seq == ["code_switching", "redundancy", "condescending"]
                else seq[0]
            ),
        ):
            out = compiler.corrupt_tonal_deviation(text, "Français")
        # inline insertion after first comma
        self.assertIn("comme n'importe quel amateur de base", out)
        self.assertTrue(out.startswith("C'est pourtant évident"))


class TestCorruptAbruptTruncationShort(unittest.TestCase):
    def test_short_text_returned_unchanged(self):
        """Line 827: text < 10 chars returned as-is."""
        self.assertEqual(compiler.corrupt_abrupt_truncation("short"), "short")


class TestCorruptLLMCriticRetry(unittest.TestCase):
    def setUp(self):
        compiler.DPO_CACHE = {}
        self._orig_client = compiler.GEMINI_CLIENT

    def tearDown(self):
        compiler.GEMINI_CLIENT = self._orig_client
        compiler.DPO_CACHE = {}

    def test_rate_limit_exception_then_fallback(self):
        """Lines 893-909: retries on 429, then falls back to fact substitution."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError(
            "429 RESOURCE_EXHAUSTED"
        )
        compiler.GEMINI_CLIENT = mock_client
        chosen = "Wit Studio a produit cet anime en 2013 avec brio."
        with (
            patch("time.sleep") as mock_sleep,
            patch.object(
                compiler,
                "corrupt_fact_substitution",
                return_value="FALLBACK RESULT",
            ) as mock_fb,
        ):
            out = compiler.corrupt_llm_critic(chosen, "Français")
        self.assertEqual(out, "FALLBACK RESULT")
        self.assertEqual(mock_client.models.generate_content.call_count, 3)
        mock_fb.assert_called_once_with(chosen, "Français")
        # Rate-limit branch uses escalating sleeps (attempt+1)*15
        self.assertIn(15.0, [c.args[0] for c in mock_sleep.call_args_list])

    def test_generic_exception_uses_short_sleep(self):
        """Lines 906-907: non-rate-limit errors sleep 1.0s between retries."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = ValueError("weird error")
        compiler.GEMINI_CLIENT = mock_client
        chosen = "Une réponse experte sur Naruto et son auteur Masashi Kishimoto."
        with (
            patch("time.sleep") as mock_sleep,
            patch.object(compiler, "corrupt_fact_substitution", return_value="FB"),
        ):
            out = compiler.corrupt_llm_critic(chosen, "Français")
        self.assertEqual(out, "FB")
        self.assertIn(1.0, [c.args[0] for c in mock_sleep.call_args_list])

    def test_empty_response_text_falls_through_to_fallback(self):
        """Lines 886-892 false branch: blank response.text -> fallback."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = ""  # falsy -> no early return
        mock_client.models.generate_content.return_value = mock_resp
        compiler.GEMINI_CLIENT = mock_client
        chosen = "Du texte expert riche sur l'animation japonaise contemporaine."
        with (
            patch("time.sleep"),
            patch.object(compiler, "corrupt_fact_substitution", return_value="FB2"),
        ):
            out = compiler.corrupt_llm_critic(chosen, "Français")
        self.assertEqual(out, "FB2")


class TestCompileDpoPairsBranches(unittest.TestCase):
    def _write_jsonl(self, path, rows):
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def test_missing_sft_no_feedback_returns_zero(self):
        """Lines 959-968: missing SFT file and no feedback => 0, no output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "missing.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            with patch.object(
                compiler, "compile_dpo_pairs", compiler.compile_dpo_pairs
            ):
                # Force the feedback loop import to yield no loop
                with patch.dict(
                    "sys.modules",
                    {
                        "dpo_feedback_loop": None,
                        "backend.pipeline.mlops.dpo_feedback_loop": None,
                    },
                ):
                    result = compiler.compile_dpo_pairs(sft, out, limit=5, seed=1)
            self.assertEqual(result, 0)
            self.assertFalse(os.path.exists(out))

    def test_missing_sft_with_feedback_writes_feedback_only(self):
        """Lines 962-967: missing SFT but feedback present => write feedback pairs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "missing.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")

            fake_loop = MagicMock()
            fake_loop.fetch_db_feedbacks.return_value = [{"x": 1}, {"x": 2}]
            fake_loop.validate_feedback.return_value = True
            fake_loop.create_dpo_pair.side_effect = [
                {"prompt": "p1", "chosen": "c1", "rejected": "r1"},
                {"prompt": "p2", "chosen": "c2", "rejected": "r2"},
            ]
            fake_loop_cls = MagicMock(return_value=fake_loop)
            fake_module = MagicMock()
            fake_module.DPOFeedbackLoop = fake_loop_cls

            with patch.dict("sys.modules", {"dpo_feedback_loop": fake_module}):
                result = compiler.compile_dpo_pairs(sft, out, limit=1, seed=1)
            # limit=1 truncates the 2 feedback pairs
            self.assertEqual(result, 1)
            with open(out, encoding="utf-8") as f:
                lines = [json.loads(x) for x in f]
            self.assertEqual(len(lines), 1)
            self.assertEqual(lines[0]["prompt"], "p1")

    def test_feedback_loop_exception_is_swallowed(self):
        """Lines 954-955: exception in feedback compilation is logged, not raised."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "sft.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            self._write_jsonl(
                sft,
                [
                    {
                        "instruction": "Parle de Wit Studio en detail.",
                        "input": "",
                        "output": "Wit Studio est un studio japonais fonde en 2012 par d'anciens de Production I.G aujourd'hui.",
                        "language": "Français",
                    }
                ],
            )
            fake_loop_cls = MagicMock(side_effect=RuntimeError("db down"))
            fake_module = MagicMock()
            fake_module.DPOFeedbackLoop = fake_loop_cls
            with patch.dict("sys.modules", {"dpo_feedback_loop": fake_module}):
                result = compiler.compile_dpo_pairs(sft, out, limit=5, seed=1)
            # SFT still processed despite feedback failure
            self.assertEqual(result, 1)

    def test_no_feedback_loop_import_available(self):
        """Lines 930-931: both imports fail => DPOFeedbackLoop is None, SFT only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "sft.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            self._write_jsonl(
                sft,
                [
                    {
                        "instruction": "Decris One Piece.",
                        "input": "",
                        "output": "One Piece est un manga de Eiichiro Oda publie depuis 1997 au Japon dans le Weekly Shonen Jump.",
                        "language": "Français",
                    }
                ],
            )
            with patch.dict(
                "sys.modules",
                {
                    "dpo_feedback_loop": None,
                    "backend.pipeline.mlops.dpo_feedback_loop": None,
                },
            ):
                result = compiler.compile_dpo_pairs(sft, out, limit=5, seed=1)
            self.assertEqual(result, 1)

    def test_rejected_equals_chosen_falls_back_to_refusal(self):
        """Line 1044: if corruption returns chosen verbatim, use evasive refusal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "sft.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            chosen = "Une reponse experte detaillee sur l'animation japonaise moderne."
            self._write_jsonl(
                sft,
                [
                    {
                        "instruction": "Question experte.",
                        "input": "",
                        "output": chosen,
                        "language": "Français",
                    }
                ],
            )
            # Force the first (fact) strategy to return chosen unchanged
            with (
                patch.object(
                    compiler, "corrupt_fact_substitution", return_value=chosen
                ),
                patch.dict(
                    "sys.modules",
                    {
                        "dpo_feedback_loop": None,
                        "backend.pipeline.mlops.dpo_feedback_loop": None,
                    },
                ),
            ):
                result = compiler.compile_dpo_pairs(sft, out, limit=1, seed=1)
            self.assertEqual(result, 1)
            with open(out, encoding="utf-8") as f:
                pair = json.loads(f.readline())
            self.assertNotEqual(pair["rejected"], pair["chosen"])

    def test_remaining_limit_zero_truncates_feedback(self):
        """Line 1055: when feedback fills the limit, SFT loop is skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "sft.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            self._write_jsonl(
                sft,
                [
                    {
                        "instruction": "Une instruction SFT distincte.",
                        "input": "",
                        "output": "Un long texte expert sur la japanimation et ses studios renommes au fil des annees.",
                        "language": "Français",
                    }
                ],
            )
            fake_loop = MagicMock()
            fake_loop.fetch_db_feedbacks.return_value = [{"a": 1}, {"a": 2}]
            fake_loop.validate_feedback.return_value = True
            fake_loop.create_dpo_pair.side_effect = [
                {"prompt": "fp1", "chosen": "fc1", "rejected": "fr1"},
                {"prompt": "fp2", "chosen": "fc2", "rejected": "fr2"},
            ]
            fake_module = MagicMock()
            fake_module.DPOFeedbackLoop = MagicMock(return_value=fake_loop)
            with patch.dict("sys.modules", {"dpo_feedback_loop": fake_module}):
                # limit == number of feedback pairs => remaining_limit == 0
                result = compiler.compile_dpo_pairs(sft, out, limit=2, seed=1)
            self.assertEqual(result, 2)
            with open(out, encoding="utf-8") as f:
                lines = [json.loads(x) for x in f]
            prompts = {ln["prompt"] for ln in lines}
            self.assertEqual(prompts, {"fp1", "fp2"})

    def test_feedback_corrupt_callback_tonal_branch(self):
        """Line 942: corrupt_callback uses tonal deviation when random < 0.5."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "missing.jsonl")  # absent on purpose
            out = os.path.join(tmpdir, "dpo.jsonl")

            captured = {}

            # Real loop-like object that exercises corrupt_callback for positive
            # feedback so the random<0.5 (tonal) branch runs.
            class FakeLoop:
                def __init__(self, data_dir):
                    pass

                def fetch_db_feedbacks(self):
                    return [{"positive": True}]

                def validate_feedback(self, fb):
                    return True

                def create_dpo_pair(self, fb, corrupt_fn):
                    captured["rejected"] = corrupt_fn(
                        "Wit Studio est un studio japonais reconnu pour son animation."
                    )
                    return {
                        "prompt": "p",
                        "chosen": "Wit Studio est un studio japonais reconnu.",
                        "rejected": captured["rejected"],
                    }

            fake_module = MagicMock()
            fake_module.DPOFeedbackLoop = FakeLoop

            with (
                patch.dict("sys.modules", {"dpo_feedback_loop": fake_module}),
                # Force random.random() < 0.5 => tonal deviation path
                patch.object(compiler.random, "random", return_value=0.1),
            ):
                result = compiler.compile_dpo_pairs(sft, out, limit=5, seed=1)

            self.assertEqual(result, 1)
            # Tonal deviation always returns a non-empty, modified string
            self.assertTrue(captured["rejected"])

    def test_feedback_corrupt_callback_refusal_branch(self):
        """Line 944: corrupt_callback uses evasive refusal when random >= 0.5."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "missing.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            captured = {}

            class FakeLoop:
                def __init__(self, data_dir):
                    pass

                def fetch_db_feedbacks(self):
                    return [{"positive": True}]

                def validate_feedback(self, fb):
                    return True

                def create_dpo_pair(self, fb, corrupt_fn):
                    captured["rejected"] = corrupt_fn("Texte expert original.")
                    return {
                        "prompt": "p",
                        "chosen": "Texte expert original.",
                        "rejected": captured["rejected"],
                    }

            fake_module = MagicMock()
            fake_module.DPOFeedbackLoop = FakeLoop

            with (
                patch.dict("sys.modules", {"dpo_feedback_loop": fake_module}),
                patch.object(compiler.random, "random", return_value=0.9),
            ):
                result = compiler.compile_dpo_pairs(sft, out, limit=5, seed=1)

            self.assertEqual(result, 1)
            # Evasive refusal returns one of the known refusal strings
            self.assertTrue(
                any(
                    kw in captured["rejected"].lower()
                    for kw in ["désolé", "aucune idée", "google"]
                )
            )

    def test_malformed_jsonl_line_skipped(self):
        """Lines 1002-1003: invalid JSON line is skipped, valid one processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sft = os.path.join(tmpdir, "sft.jsonl")
            out = os.path.join(tmpdir, "dpo.jsonl")
            with open(sft, "w", encoding="utf-8") as f:
                f.write("{ not valid json\n")
                f.write(
                    json.dumps(
                        {
                            "instruction": "Decris Bleach.",
                            "input": "",
                            "output": "Bleach est un manga de Tite Kubo publie de 2001 a 2016 dans le Weekly Shonen Jump.",
                            "language": "Français",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                # Entry missing required keys (line 988 continue)
                f.write(json.dumps({"foo": "bar"}, ensure_ascii=False) + "\n")
            with patch.dict(
                "sys.modules",
                {
                    "dpo_feedback_loop": None,
                    "backend.pipeline.mlops.dpo_feedback_loop": None,
                },
            ):
                result = compiler.compile_dpo_pairs(sft, out, limit=5, seed=1)
            self.assertEqual(result, 1)


class TestMainEntryPoint(unittest.TestCase):
    def test_main_invokes_compile_with_env(self):
        """Lines 1071-1086: __main__ block parses env and calls compile_dpo_pairs.

        runpy.run_path executes the real source file under __name__ == "__main__"
        (so coverage attributes the guard lines correctly). The freshly executed
        module defines and calls its own compile_dpo_pairs, so it can't be spied
        on via the cached import. Instead we mask the default SFT path as absent
        (see below) so the real compile_dpo_pairs takes its no-op branch — a
        safe, hermetic run with no LLM/DB/file output.
        """
        import runpy

        src_path = compiler.__file__
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(src_path))))
        )
        sft_default = os.path.join(
            base_dir, "data", "mlops", "datasets", "animetix_expert_ft.jsonl"
        )
        dpo_default = os.path.join(
            base_dir, "data", "mlops", "datasets", "dpo_train_validated.jsonl"
        )
        existed_before = os.path.exists(dpo_default)

        # Force the default SFT dataset to read as absent so the real
        # compile_dpo_pairs invoked by __main__ takes its no-op path (line 961:
        # missing SFT + no feedback => return 0, write nothing). This makes the
        # test hermetic whether or not a developer has generated the (gitignored)
        # 50 MB SFT dataset locally; in CI the file is simply absent. Only the
        # SFT path is masked — every other path delegates to the real check so
        # runpy can still locate the source file.
        real_exists = os.path.exists

        def _exists_without_sft(path):
            if os.path.abspath(path) == os.path.abspath(sft_default):
                return False
            return real_exists(path)

        # Block the optional Django feedback-loop import so the run touches no DB.
        with (
            patch.dict(
                os.environ,
                {"ANIMETIX_DPO_SIZE": "7", "ANIMETIX_DPO_SEED": "13"},
                clear=False,
            ),
            patch.dict(
                "sys.modules",
                {
                    "dpo_feedback_loop": None,
                    "backend.pipeline.mlops.dpo_feedback_loop": None,
                },
            ),
            patch("os.path.exists", side_effect=_exists_without_sft),
        ):
            # Executes the real source file with __name__ == "__main__",
            # covering the env-parsing and compile_dpo_pairs call site.
            runpy.run_path(src_path, run_name="__main__")

        # Real behavior: missing SFT => no output dataset was created.
        if not existed_before:
            self.assertFalse(os.path.exists(dpo_default))


if __name__ == "__main__":
    unittest.main()
