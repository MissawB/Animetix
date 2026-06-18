# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import json


class TestDPODatasetCompiler(unittest.TestCase):
    def setUp(self):
        # We dynamic import to allow tests to load after implementation exists
        pass

    def test_corrupt_fact_substitution(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import (
            corrupt_fact_substitution,
        )  # noqa: E402

        # Test years/numbers substitution (fallback)
        text_num = "Cet anime est sorti en 2018 avec 24 épisodes."
        corr_num = corrupt_fact_substitution(text_num, "Français")
        self.assertNotEqual(text_num, corr_num)
        self.assertTrue(
            any(
                str(year) in corr_num
                for year in range(1980, 2027)
                if str(year) != "2018"
            )
        )

        # Test studio close-concept replacement
        text_studio = "L'anime a été produit par Wit Studio."
        corr_studio = corrupt_fact_substitution(text_studio, "Français")
        self.assertNotEqual(text_studio, corr_studio)

        text_ufotable = "L'anime a été produit par ufotable."
        corr_ufo = corrupt_fact_substitution(text_ufotable, "Français")
        self.assertNotEqual(text_ufotable, corr_ufo)
        self.assertTrue(
            any(
                s in corr_ufo
                for s in [
                    "MAPPA",
                    "Studio Trigger",
                    "Bones",
                    "Sunrise",
                    "Wit Studio",
                    "Studio Ghibli",
                    "Kyoto Animation",
                    "Madhouse",
                    "Studio Pierrot",
                ]
            )
        )

        # Test voice actor franchise replacement
        text_va = "Son Goku est doublé par Brigitte Lecordier."
        corr_va = corrupt_fact_substitution(text_va, "Français")
        self.assertNotEqual(text_va, corr_va)
        self.assertTrue(
            any(
                v in corr_va
                for v in ["Patrick Borg", "Eric Legrand", "Philippe Ariotti"]
            )
        )

        # Test publisher group replacement
        text_pub = "Le manga est édité par Glénat Manga."
        corr_pub = corrupt_fact_substitution(text_pub, "Français")
        self.assertNotEqual(text_pub, corr_pub)
        self.assertTrue(
            any(
                p in corr_pub
                for p in [
                    "Kana",
                    "Pika Édition",
                    "Kurokawa",
                    "Ki-oon",
                    "Crunchyroll Manga",
                ]
            )
        )

    def test_corrupt_tonal_deviation(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_tonal_deviation  # noqa: E402

        text = "Cet anime est un chef-d'œuvre avec d'excellents personnages. C'est incroyable !"

        strategies_seen = {
            "code_switching": False,
            "redundancy": False,
            "condescending": False,
        }

        for _ in range(50):
            corr = corrupt_tonal_deviation(text, "Français")
            # 1. Code-switching check
            if (
                "masterpiece" in corr
                or "character" in corr
                or "basically" in corr.lower()
            ):
                strategies_seen["code_switching"] = True
            # 2. Redundancy check
            if "préciser" in corr or "explication" in corr or "répète" in corr.lower():
                strategies_seen["redundancy"] = True
            # 3. Condescending check
            if (
                "évident" in corr
                or "otaku" in corr
                or "Franchement" in corr
                or "triviale" in corr
            ):
                strategies_seen["condescending"] = True

        self.assertTrue(
            strategies_seen["code_switching"],
            "Code-switching strategy was not triggered",
        )
        self.assertTrue(
            strategies_seen["redundancy"], "Redundancy strategy was not triggered"
        )
        self.assertTrue(
            strategies_seen["condescending"], "Condescending strategy was not triggered"
        )

    def test_corrupt_abrupt_truncation(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import (
            corrupt_abrupt_truncation,
        )  # noqa: E402

        text = "C'est un long texte informatif sur la japanimation avec beaucoup de détails techniques sur les doubleurs français."
        corr = corrupt_abrupt_truncation(text)

        self.assertTrue(len(corr) < len(text))
        self.assertTrue(len(corr) >= len(text) * 0.25)  # Safe bounds
        # Should not end with clean sentence completion punctuation
        self.assertFalse(corr.endswith("."))

    def test_corrupt_evasive_refusal(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_evasive_refusal  # noqa: E402

        text = "Voici les informations complètes sur Sword Art Online."

        corr_fr = corrupt_evasive_refusal(text, "Français")
        self.assertTrue(any(x in corr_fr.lower() for x in ["désolé", "aucune idée"]))

        corr_en = corrupt_evasive_refusal(text, "English")
        self.assertTrue(any(x in corr_en.lower() for x in ["sorry", "don't know"]))

    def test_compile_dpo_pairs(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import compile_dpo_pairs  # noqa: E402

        # Setup mock SFT dataset
        mock_data = [
            # 1. Valid entry (long enough)
            {
                "instruction": "Explique l'importance de Wit Studio.",
                "input": "",
                "output": "Wit Studio est un studio d'animation japonais de premier plan fondé en juin 2012 par des producteurs de Production I.G.",
                "language": "Français",
            },
            # 2. Too short (should be filtered out)
            {
                "instruction": "Qui est Luffy ?",
                "input": "",
                "output": "Le héros de One Piece.",
                "language": "Français",
            },
            # 3. Refusal (should be filtered out)
            {
                "instruction": "Donne moi des leaks.",
                "input": "",
                "output": "Désolé, je ne dispose pas d'informations sur des rumeurs ou leaks non confirmés.",
                "language": "Français",
            },
            # 4. Another valid entry
            {
                "instruction": "What is the release year of Death Note?",
                "input": "",
                "output": "The anime adaptation of Death Note was produced by Madhouse and aired in Japan in 2006.",
                "language": "English",
            },
            # 5. Third valid entry
            {
                "instruction": "Parle moi de My Hero Academia.",
                "input": "",
                "output": "My Hero Academia est un manga shonen écrit et dessiné par Kohei Horikoshi depuis 2014.",
                "language": "Français",
            },
            # 6. Fourth valid entry
            {
                "instruction": "Qui est Gojo Satoru ?",
                "input": "",
                "output": "Gojo Satoru est le puissant mentor dans le manga Jujutsu Kaisen créé par Gege Akutami.",
                "language": "Français",
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            sft_file = os.path.join(tmpdir, "sft.jsonl")
            output_file = os.path.join(tmpdir, "dpo.jsonl")

            with open(sft_file, "w", encoding="utf-8") as f:
                for item in mock_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            # Compile DPO pairs (requesting 4 pairs)
            compiled_count = compile_dpo_pairs(sft_file, output_file, limit=4, seed=42)

            # 4 of them are valid (>40 chars, no refusal). Limit is 4. So we expect 4 compiled pairs.
            self.assertEqual(compiled_count, 4)

            # Check output file contents
            self.assertTrue(os.path.exists(output_file))
            with open(output_file, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f]

            self.assertEqual(len(lines), 4)
            for item in lines:
                self.assertIn("prompt", item)
                self.assertIn("chosen", item)
                self.assertIn("rejected", item)
                self.assertNotEqual(item["chosen"], item["rejected"])

    def test_compile_dpo_pairs_with_db_feedback(self):
        import sys  # noqa: E402
        import os  # noqa: E402

        # Ensure mlops directory is in path for mock import resolution
        mlops_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "backend", "pipeline", "mlops"
            )
        )
        if mlops_path not in sys.path:
            sys.path.insert(0, mlops_path)

        from unittest.mock import patch, MagicMock  # noqa: E402
        from backend.pipeline.mlops.dpo_dataset_compiler import compile_dpo_pairs  # noqa: E402

        # Mocking fetch_db_feedbacks to simulate user feedback entries
        mock_feedbacks = [
            # 1. Thumbs up feedback (should trigger positive DPO pair generation)
            {
                "context": "Qui est Shinji Ikari ?",
                "output": "Shinji Ikari est le protagoniste de Neon Genesis Evangelion, un adolescent complexe qui pilote l'EVA-01.",
                "is_positive": True,
                "feedback_type": "thumbs_up",
            },
            # 2. Thumbs down feedback (should trigger Gemini Oracle chosen generation)
            {
                "context": "Quel studio a fait Demon Slayer ?",
                "output": "C'est MAPPA, non ?",
                "is_positive": False,
                "feedback_type": "thumbs_down",
            },
        ]

        with (
            patch("dpo_feedback_loop.django_available", True),
            patch("backend.pipeline.mlops.dpo_feedback_loop.django_available", True),
            patch("dpo_feedback_loop.AIFeedback") as mock_ai_feedback,
            patch(
                "backend.pipeline.mlops.dpo_feedback_loop.AIFeedback", mock_ai_feedback
            ),
        ):
            # Setup mock model query results
            mock_entries = []
            for fb in mock_feedbacks:
                mock_fb = MagicMock()
                mock_fb.input_context = fb["context"]
                mock_fb.output_text = fb["output"]
                mock_fb.is_positive = fb["is_positive"]
                mock_fb.feedback_type = fb["feedback_type"]
                mock_entries.append(mock_fb)

            mock_ai_feedback.objects.all.return_value = mock_entries

            # Mock generate_oracle_response to return a valid chosen response for negative feedback
            with (
                patch(
                    "dpo_feedback_loop.DPOFeedbackLoop.generate_oracle_response"
                ) as mock_oracle,
                patch(
                    "backend.pipeline.mlops.dpo_feedback_loop.DPOFeedbackLoop.generate_oracle_response",
                    mock_oracle,
                ),
            ):
                mock_oracle.return_value = "Demon Slayer a été produit par le studio ufotable, connu pour son animation de haute qualité."

                import tempfile  # noqa: E402

                with tempfile.TemporaryDirectory() as tmpdir:
                    sft_file = os.path.join(tmpdir, "sft.jsonl")
                    output_file = os.path.join(tmpdir, "dpo.jsonl")

                    # Create empty SFT file so compiler only outputs feedback pairs
                    with open(sft_file, "w", encoding="utf-8") as f:
                        pass

                    compiled_count = compile_dpo_pairs(
                        sft_file, output_file, limit=5, seed=42
                    )

                    # We expect 2 pairs compiled (both mock feedbacks validated and converted)
                    self.assertEqual(compiled_count, 2)

                    with open(output_file, "r", encoding="utf-8") as f:
                        lines = [json.loads(line) for line in f]

                    self.assertEqual(len(lines), 2)

                    # Verify positive feedback pair
                    p1 = lines[0]
                    self.assertEqual(
                        p1["prompt"],
                        "Génère une réponse expert pour : Qui est Shinji Ikari ?",
                    )
                    self.assertEqual(
                        p1["chosen"],
                        "Shinji Ikari est le protagoniste de Neon Genesis Evangelion, un adolescent complexe qui pilote l'EVA-01.",
                    )
                    self.assertNotEqual(p1["rejected"], p1["chosen"])

                    # Verify negative feedback pair
                    p2 = lines[1]
                    self.assertEqual(
                        p2["prompt"],
                        "Génère une réponse expert pour : Quel studio a fait Demon Slayer ?",
                    )
                    self.assertEqual(
                        p2["chosen"],
                        "Demon Slayer a été produit par le studio ufotable, connu pour son animation de haute qualité.",
                    )
                    self.assertEqual(p2["rejected"], "C'est MAPPA, non ?")

    def test_dpo_cache_read_write(self):
        import tempfile  # noqa: E402
        import os  # noqa: E402
        import backend.pipeline.mlops.dpo_dataset_compiler as compiler  # noqa: E402

        with tempfile.TemporaryDirectory() as tmpdir:
            compiler.init_dpo_cache(tmpdir)
            # Cache should be empty initially
            self.assertEqual(compiler.DPO_CACHE, {})

            # Insert a mock entry
            compiler.DPO_CACHE["test_hash"] = "test_corrupted"
            compiler.save_dpo_cache()

            # Check file exists
            cache_file = os.path.join(tmpdir, "gemini_dpo_cache.json")
            self.assertTrue(os.path.exists(cache_file))

            # Re-initialize should load it back
            compiler.init_dpo_cache(tmpdir)
            self.assertEqual(compiler.DPO_CACHE.get("test_hash"), "test_corrupted")

    def test_corrupt_llm_critic(self):
        from unittest.mock import MagicMock  # noqa: E402
        import backend.pipeline.mlops.dpo_dataset_compiler as compiler  # noqa: E402

        # Reset mock state
        compiler.DPO_CACHE = {}
        compiler.GEMINI_CLIENT = None

        # 1. Test offline/missing API key fallback
        chosen = "Le studio Wit Studio a produit L'Attaque des Titans."
        corrupted = compiler.corrupt_llm_critic(chosen, "Français")
        # Fallback should run and modify the text
        self.assertNotEqual(corrupted, chosen)

        # 2. Test cache hits
        chosen_hash = compiler.hashlib.md5(chosen.encode("utf-8")).hexdigest()
        compiler.DPO_CACHE[chosen_hash] = "Cached mock response"
        corrupted_cached = compiler.corrupt_llm_critic(chosen, "Français")
        self.assertEqual(corrupted_cached, "Cached mock response")

        # 3. Test active API call mock
        compiler.DPO_CACHE = {}
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini mocked logical error response."
        mock_client.models.generate_content.return_value = mock_response
        compiler.GEMINI_CLIENT = mock_client

        corrupted_api = compiler.corrupt_llm_critic(chosen, "Français")
        self.assertEqual(corrupted_api, "Gemini mocked logical error response.")
        self.assertEqual(
            compiler.DPO_CACHE[chosen_hash], "Gemini mocked logical error response."
        )

    def test_compile_dpo_pairs_llm_strategy_in_rotation(self):
        """Verify that the 'llm' strategy is part of compile_dpo_pairs rotation (~20%)."""
        from unittest.mock import patch  # noqa: E402
        import tempfile  # noqa: E402
        import backend.pipeline.mlops.dpo_dataset_compiler as compiler  # noqa: E402

        # Create a SFT dataset with 10 valid entries to observe strategy distribution
        mock_data = []
        for i in range(10):
            mock_data.append(
                {
                    "instruction": f"Question numéro {i} sur l'animation japonaise et ses créateurs.",
                    "input": "",
                    "output": f"Réponse détaillée numéro {i} sur Wit Studio et le manga Naruto sorti en 2002 avec Madhouse. Cet anime est incroyable.",
                    "language": "Français",
                }
            )

        # Track which strategies are called
        call_log = {"llm": 0, "fact": 0, "tone": 0, "truncation": 0, "refusal": 0}
        original_corrupt_fact = compiler.corrupt_fact_substitution
        original_corrupt_tone = compiler.corrupt_tonal_deviation
        original_corrupt_trunc = compiler.corrupt_abrupt_truncation
        original_corrupt_refusal = compiler.corrupt_evasive_refusal

        def mock_llm(chosen, lang="Français"):
            call_log["llm"] += 1
            return "LLM corrupted: " + chosen[:30]

        def mock_fact(text, lang="Français"):
            call_log["fact"] += 1
            return original_corrupt_fact(text, lang)

        def mock_tone(text, lang="Français"):
            call_log["tone"] += 1
            return original_corrupt_tone(text, lang)

        def mock_trunc(text):
            call_log["truncation"] += 1
            return original_corrupt_trunc(text)

        def mock_refusal(text, lang="Français"):
            call_log["refusal"] += 1
            return original_corrupt_refusal(text, lang)

        with tempfile.TemporaryDirectory() as tmpdir:
            sft_file = os.path.join(tmpdir, "sft.jsonl")
            output_file = os.path.join(tmpdir, "dpo.jsonl")

            with open(sft_file, "w", encoding="utf-8") as f:
                for item in mock_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            with (
                patch.object(compiler, "corrupt_llm_critic", side_effect=mock_llm),
                patch.object(
                    compiler, "corrupt_fact_substitution", side_effect=mock_fact
                ),
                patch.object(
                    compiler, "corrupt_tonal_deviation", side_effect=mock_tone
                ),
                patch.object(
                    compiler, "corrupt_abrupt_truncation", side_effect=mock_trunc
                ),
                patch.object(
                    compiler, "corrupt_evasive_refusal", side_effect=mock_refusal
                ),
            ):
                compiled_count = compiler.compile_dpo_pairs(
                    sft_file, output_file, limit=10, seed=42
                )

            self.assertEqual(compiled_count, 10)

            # "llm" should be one of the 5 strategies in the rotation
            # With 10 entries and 5 strategies (round-robin), we expect exactly 2 LLM calls
            self.assertEqual(
                call_log["llm"], 2, f"Expected 2 LLM calls (20%), got {call_log['llm']}"
            )

            # All 5 strategies should have been used
            for strat in ["fact", "tone", "truncation", "refusal", "llm"]:
                self.assertGreater(
                    call_log[strat], 0, f"Strategy '{strat}' was never called"
                )


class TestDPOSampleValidator(unittest.TestCase):
    """Tests for Pydantic schema validation of DPO samples."""

    def test_valid_sample_passes(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402

        sample = DPOSampleValidator(
            prompt="Qui est le créateur de Naruto ?",
            chosen="Naruto a été créé par Masashi Kishimoto et publié dans le Weekly Shōnen Jump depuis 1999.",
            rejected="Naruto a été créé par Eiichiro Oda et publié dans le Monthly Shōnen Magazine.",
        )
        self.assertEqual(sample.prompt, "Qui est le créateur de Naruto ?")

    def test_rejects_html_residues_in_chosen(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402
        from pydantic import ValidationError  # noqa: E402

        with self.assertRaises(ValidationError) as ctx:
            DPOSampleValidator(
                prompt="Explique l'anime.",
                chosen="<div>Cet anime est produit par <b>MAPPA</b></div>",
                rejected="Je ne sais pas.",
            )
        self.assertIn("chosen", str(ctx.exception))

    def test_rejects_html_residues_in_rejected(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402
        from pydantic import ValidationError  # noqa: E402

        with self.assertRaises(ValidationError) as ctx:
            DPOSampleValidator(
                prompt="Explique l'anime.",
                chosen="Cet anime est produit par MAPPA.",
                rejected="<p>Réponse mal formatée</p>",
            )
        self.assertIn("rejected", str(ctx.exception))

    def test_rejects_malformed_code_blocks(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402
        from pydantic import ValidationError  # noqa: E402

        # Unclosed code block
        with self.assertRaises(ValidationError):
            DPOSampleValidator(
                prompt="Question valide.",
                chosen="Voici du code ```python\nprint('hello')\n sans fermer le bloc.",
                rejected="Réponse correcte et propre sans résidu de formatage.",
            )

    def test_rejects_failed_api_response(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402
        from pydantic import ValidationError  # noqa: E402

        api_failures = [
            "Error: Internal Server Error",
            '{"error": "rate_limit_exceeded"}',
            "500 Internal Server Error",
            "<!DOCTYPE html><html>Error page</html>",
        ]
        for fail_text in api_failures:
            with self.assertRaises(
                ValidationError, msg=f"Should reject: {fail_text!r}"
            ):
                DPOSampleValidator(
                    prompt="Question valide.",
                    chosen=fail_text,
                    rejected="Réponse correcte.",
                )

    def test_rejects_empty_or_whitespace(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402
        from pydantic import ValidationError  # noqa: E402

        with self.assertRaises(ValidationError):
            DPOSampleValidator(
                prompt="  ", chosen="Texte valide.", rejected="Texte valide."
            )
        with self.assertRaises(ValidationError):
            DPOSampleValidator(prompt="Question.", chosen="", rejected="Texte valide.")
        with self.assertRaises(ValidationError):
            DPOSampleValidator(
                prompt="Question.", chosen="Texte valide.", rejected="   "
            )

    def test_rejects_identical_chosen_rejected(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import DPOSampleValidator  # noqa: E402
        from pydantic import ValidationError  # noqa: E402

        with self.assertRaises(ValidationError):
            DPOSampleValidator(
                prompt="Question.",
                chosen="Exactement la même réponse.",
                rejected="Exactement la même réponse.",
            )

    def test_compile_dpo_pairs_filters_invalid_samples(self):
        """Integration: compile_dpo_pairs should skip samples that fail Pydantic validation."""
        from unittest.mock import patch  # noqa: E402
        import tempfile  # noqa: E402
        import backend.pipeline.mlops.dpo_dataset_compiler as compiler  # noqa: E402

        # 5 entries: the corruption function will return HTML for some
        mock_data = [
            {
                "instruction": "Q1 sur l'animation japonaise.",
                "input": "",
                "output": "Wit Studio est un studio d'animation fondé en 2012.",
                "language": "Français",
            },
            {
                "instruction": "Q2 sur les mangas japonais.",
                "input": "",
                "output": "One Piece est un manga de Eiichiro Oda depuis 1997 au Japon.",
                "language": "Français",
            },
            {
                "instruction": "Q3 sur les doubleurs français.",
                "input": "",
                "output": "Brigitte Lecordier est une doubleuse française très connue de Dragon Ball Z.",
                "language": "Français",
            },
        ]

        call_count = {"idx": 0}

        def mock_corrupt_fact(text, lang="Français"):
            call_count["idx"] += 1
            if call_count["idx"] == 1:
                # Return HTML residue — should be filtered
                return "<div>Réponse cassée avec du HTML</div>"
            return (
                compiler.corrupt_fact_substitution.__wrapped__(text, lang)
                if hasattr(compiler.corrupt_fact_substitution, "__wrapped__")
                else "MAPPA est un studio d'animation fondé en 2011."
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            sft_file = os.path.join(tmpdir, "sft.jsonl")
            output_file = os.path.join(tmpdir, "dpo.jsonl")

            with open(sft_file, "w", encoding="utf-8") as f:
                for item in mock_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            with patch.object(
                compiler, "corrupt_fact_substitution", side_effect=mock_corrupt_fact
            ):
                compiler.compile_dpo_pairs(sft_file, output_file, limit=3, seed=42)

            # At least one sample should have been filtered out
            with open(output_file, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f]

            # No line should contain HTML tags
            for line in lines:
                self.assertNotRegex(line["chosen"], r"<[a-zA-Z][^>]*>")
                self.assertNotRegex(line["rejected"], r"<[a-zA-Z][^>]*>")


if __name__ == "__main__":
    unittest.main()
