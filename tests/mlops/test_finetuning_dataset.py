import contextlib
import json
import os
import random as _py_random
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import backend.pipeline.mlops.finetuning_dataset as fd  # noqa: E402
from backend.pipeline.mlops.finetuning_dataset import clean_description  # noqa: E402


class TestFinetuningDataset(unittest.TestCase):
    def test_clean_description(self):
        raw_text = "L'anime <i>SnK</i> est culte.<br> &quot;Incroyable&quot; &#039;chef-d'oeuvre&#039;  et   magnifique."
        expected = (
            "L'anime SnK est culte. \"Incroyable\" 'chef-d'oeuvre' et magnifique."
        )
        self.assertEqual(clean_description(raw_text), expected)

    def test_gemini_paraphrase_cache(self):
        from unittest.mock import MagicMock  # noqa: E402

        # Cache + fonctions paraphrase vivent désormais dans ft_dataset.paraphrase
        import backend.pipeline.mlops.ft_dataset.paraphrase as pmod  # noqa: E402
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            paraphrase_text_via_gemini,
        )

        pmod.PARAPHRASE_CACHE = {
            "Le texte original||naturel": "Texte paraphrase en cache"
        }

        # Mocker le client Gemini
        mock_client = MagicMock()

        # Premier appel : doit retourner la valeur du cache sans interroger le client
        res1 = paraphrase_text_via_gemini("Le texte original", mock_client, "naturel")
        self.assertEqual(res1, "Texte paraphrase en cache")
        mock_client.models.generate_content.assert_not_called()

        # Deuxième appel : clé manquante, doit interroger le client et alimenter le cache
        mock_response = MagicMock()
        mock_response.text = "Nouvelle paraphrase"
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "backend.pipeline.mlops.ft_dataset.paraphrase.validate_factual_alignment",
            return_value=True,
        ):
            res2 = paraphrase_text_via_gemini("Un autre texte", mock_client, "naturel")
            self.assertEqual(res2, "Nouvelle paraphrase")
            mock_client.models.generate_content.assert_called_once()
            self.assertIn("Un autre texte||naturel", pmod.PARAPHRASE_CACHE)
            self.assertEqual(
                pmod.PARAPHRASE_CACHE["Un autre texte||naturel"], "Nouvelle paraphrase"
            )

    def test_configurable_ratios(self):
        from unittest.mock import patch  # noqa: E402

        import backend.pipeline.mlops.finetuning_dataset as fd  # noqa: E402

        env_vars = {
            "ANIMETIX_RATIO_SPECIALIZED": "70",
            "ANIMETIX_RATIO_META": "10",
            "ANIMETIX_RATIO_GENERAL": "20",
        }

        with patch.dict(os.environ, env_vars):
            meta_req, gen_req = fd.calculate_dataset_counts(700)
            self.assertEqual(meta_req, 100)
            self.assertEqual(gen_req, 200)

    def test_mcp_error_scenarios(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_mcp_tool_instructions,
        )

        instructions = generate_mcp_tool_instructions()

        # Vérifier la présence d'au moins un scénario contenant une réponse d'erreur de tool_response
        error_found = False
        for inst in instructions:
            if (
                "<tool_response>" in inst["input"]
                and '"status": "error"' in inst["input"]
            ):
                error_found = True
                # Vérifier que l'output contient une excuse ou indique une recherche en mémoire/connaissance
                self.assertTrue(
                    "rencontre une erreur" in inst["output"]
                    or "indisponible" in inst["output"]
                    or "limite de requêtes" in inst["output"]
                    or "désolé" in inst["output"].lower()
                    or "connaissances" in inst["output"]
                )
                break

        self.assertTrue(
            error_found, "Aucun scénario d'erreur MCP trouvé dans les instructions."
        )

    def test_bilingual_generators(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            make_english_anime_profile,
            make_english_character_bio,
            make_english_manga_profile,
        )

        # Test anime profile
        anime_prof = make_english_anime_profile(
            "Naruto", ["Action"], ["Pierrot"], ["Ninja"], 2002
        )
        self.assertIn("Naruto", anime_prof)
        self.assertIn("Action", anime_prof)
        self.assertIn("Pierrot", anime_prof)
        self.assertIn("Ninja", anime_prof)
        self.assertIn("2002", anime_prof)

        # Test manga profile
        manga_prof = make_english_manga_profile("One Piece", ["Adventure"], ["Pirates"])
        self.assertIn("One Piece", manga_prof)
        self.assertIn("Adventure", manga_prof)
        self.assertIn("Pirates", manga_prof)

        # Test character bio
        char_bio = make_english_character_bio(
            "Luffy", "One Piece", ["Straw Hats"], 150000, 1, "174cm"
        )
        self.assertIn("Luffy", char_bio)
        self.assertIn("One Piece", char_bio)
        self.assertIn("Straw Hats", char_bio)
        self.assertIn("150,000", char_bio)
        self.assertIn("174cm", char_bio)

    @patch("backend.pipeline.mlops.finetuning_dataset.load_dataset")
    def test_bilingual_general_instructions(self, mock_load_dataset):
        mock_ds_fr = [{"instruction": "Inst FR", "input": "", "output": "Rep FR"}]
        mock_ds_en = [{"instruction": "Inst EN", "input": "", "output": "Rep EN"}]

        def side_effect(path, split=None, **kwargs):
            if "alpaca-cleaned-fr" in path:
                return mock_ds_fr
            else:
                return mock_ds_en

        mock_load_dataset.side_effect = side_effect

        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            fetch_general_instructions,
        )

        res = fetch_general_instructions(2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["language"], "Français")
        self.assertEqual(res[1]["language"], "English")

    def test_generate_otaku_meta_instructions_bilingual(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_otaku_meta_instructions,
        )

        res = generate_otaku_meta_instructions(client=None)

        fr_count = sum(1 for item in res if item.get("language") == "Français")
        en_count = sum(1 for item in res if item.get("language") == "English")
        self.assertGreater(fr_count, 0)
        self.assertGreater(en_count, 0)

        en_items = [item for item in res if item.get("language") == "English"]
        self.assertTrue(
            any(
                "What does" in item["instruction"]
                or "Who is" in item["instruction"]
                or "What is the" in item["instruction"]
                for item in en_items
            )
        )

    def test_deduplicate_dataset_multiturn(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            deduplicate_dataset,
        )

        dataset = [
            {"turns": [{"user": "Hi", "assistant": "Hello"}], "language": "English"},
            {"turns": [{"user": "Hi", "assistant": "Hello"}], "language": "English"},
            {
                "instruction": "Hi",
                "input": "",
                "output": "Hello",
                "language": "English",
            },
        ]
        res = deduplicate_dataset(dataset)
        self.assertEqual(len(res), 2)

    def test_generate_multiturn_dialogues(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_multiturn_dialogues,
        )

        animes = [
            {
                "title": "Naruto",
                "genres": ["Action"],
                "studios": ["Pierrot"],
                "tags": ["Ninja"],
                "popularity": 1000000,
                "year": 2002,
            }
        ]
        mangas = [
            {
                "title": "One Piece",
                "genres": ["Adventure"],
                "tags": ["Pirates"],
                "popularity": 1500000,
            }
        ]
        chars = [
            {
                "name": "Luffy",
                "origin": "One Piece",
                "entities": {"organizations": ["Straw Hats"]},
                "popularity": {"favourites": 150000, "rank": 1},
                "metadata": {"height": "174cm"},
            }
        ]
        vocab = {
            "Tsundere": {
                "definition": "Cold then hot",
                "examples": "Taiga",
                "impact": "Popular trope",
                "origin": "Japanese",
            }
        }

        dialogues = generate_multiturn_dialogues(animes, mangas, chars, vocab, count=6)
        self.assertEqual(len(dialogues), 6)
        for d in dialogues:
            self.assertIn("turns", d)
            self.assertGreaterEqual(len(d["turns"]), 2)
            self.assertIn(d["language"], ["Français", "English"])

    def test_generate_multiturn_dialogues_complex_scenarios(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_multiturn_dialogues,
        )

        animes = [
            {
                "title": "Naruto",
                "genres": ["Action"],
                "studios": ["Pierrot"],
                "tags": ["Ninja"],
                "popularity": 1000000,
                "year": 2002,
            },
            {
                "title": "One Piece",
                "genres": ["Adventure"],
                "studios": ["Toei Animation"],
                "tags": ["Pirates"],
                "popularity": 1500000,
                "year": 1999,
            },
        ]
        mangas = [
            {
                "title": "One Piece",
                "genres": ["Adventure"],
                "tags": ["Pirates"],
                "popularity": 1500000,
            }
        ]
        chars = [
            {
                "name": "Luffy",
                "origin": "One Piece",
                "entities": {"organizations": ["Straw Hats"]},
                "popularity": {"favourites": 150000, "rank": 1},
                "metadata": {"height": "174cm"},
            },
            {
                "name": "Naruto Uzumaki",
                "origin": "Naruto",
                "entities": {"organizations": ["Konoha"]},
                "popularity": {"favourites": 100000, "rank": 2},
                "metadata": {"height": "166cm"},
            },
        ]
        vocab = {
            "Tsundere": {
                "definition": "Cold then hot",
                "examples": "Taiga",
                "impact": "Popular trope",
                "origin": "Japanese",
            }
        }

        dialogues = generate_multiturn_dialogues(animes, mangas, chars, vocab, count=14)
        self.assertEqual(len(dialogues), 14)

        # Verify comparative debate (scenario 3 -> indices 3 and 10)
        d_debate_en = dialogues[10]
        d_debate_fr = dialogues[3]
        self.assertEqual(d_debate_en["language"], "English")
        self.assertEqual(d_debate_fr["language"], "Français")
        self.assertIn("compare two major anime", d_debate_en["turns"][0]["user"])
        self.assertIn("comparer deux", d_debate_fr["turns"][0]["user"])

        # Verify clarification request (scenario 4 -> indices 4 and 11)
        d_clarif_en = dialogues[11]
        d_clarif_fr = dialogues[4]
        self.assertEqual(d_clarif_en["language"], "English")
        self.assertEqual(d_clarif_fr["language"], "Français")
        self.assertTrue(
            "popular" in d_clarif_en["turns"][0]["user"].lower()
            or "character" in d_clarif_en["turns"][0]["user"].lower()
            or "adaptation" in d_clarif_en["turns"][0]["user"].lower()
        )
        self.assertTrue(
            "populaire" in d_clarif_fr["turns"][0]["user"].lower()
            or "personnage" in d_clarif_fr["turns"][0]["user"].lower()
            or "adaptation" in d_clarif_fr["turns"][0]["user"].lower()
        )

        # Verify progressive recommendation (scenario 5 -> indices 5 and 12)
        d_prog_en = dialogues[12]
        d_prog_fr = dialogues[5]
        self.assertEqual(d_prog_en["language"], "English")
        self.assertEqual(d_prog_fr["language"], "Français")
        self.assertIn("looking for a good", d_prog_en["turns"][0]["user"])
        self.assertIn("Je cherche un bon anime de type", d_prog_fr["turns"][0]["user"])

        # Verify self-correction (scenario 6 -> indices 6 and 13)
        d_corr_en = dialogues[13]
        d_corr_fr = dialogues[6]
        self.assertEqual(d_corr_en["language"], "English")
        self.assertEqual(d_corr_fr["language"], "Français")
        self.assertIn("produced", d_corr_en["turns"][0]["user"])
        self.assertIn("occupé", d_corr_fr["turns"][0]["user"])

    def test_run_generate_instruction_dataset_contains_multiturn(self):
        import json  # noqa: E402

        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            OUTPUT_DATASET,
        )

        if os.path.exists(OUTPUT_DATASET):
            multiturn_found = False
            with open(OUTPUT_DATASET, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    if "turns" in item:
                        multiturn_found = True
                        break
            self.assertTrue(
                multiturn_found, "Compilation did not produce multi-turn examples"
            )

    def test_generate_negative_refusal_examples(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_negative_refusal_examples,
        )

        refusals = generate_negative_refusal_examples(count=10)
        self.assertEqual(len(refusals), 10)
        for item in refusals:
            self.assertIn("instruction", item)
            self.assertIn("output", item)
            self.assertIn(item["language"], ["Français", "English"])
            # Output should contain Animetix or expertise keywords
            out_lower = item["output"].lower()
            self.assertTrue(
                "animetix" in out_lower
                or "expertise" in out_lower
                or "expert" in out_lower,
                f"Refusal output must contain Animetix or expertise keywords: {item['output']}",
            )

    def test_refusal_topic_diversity(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_negative_refusal_examples,
        )

        # Generate enough refusals to cover all categories (11 categories * 2 languages = 22 variations)
        refusals = generate_negative_refusal_examples(count=400)

        # Find which topics are covered in the outputs
        french_topics_found = set()
        english_topics_found = set()

        # We can map from output keywords/topic names back to the category keys
        french_mapping = {
            "les recettes de cuisine": "recette",
            "la programmation informatique": "programmation",
            "les mathématiques": "mathematiques",
            "les conseils médicaux": "medecine",
            "la finance et les investissements": "finance",
            "l'histoire ou la géographie générale": "histoire_geo",
            "la rédaction générale": "redaction",
            "les sciences et les technologies": "science_technologie",
            "la pop culture occidentale": "pop_culture_occidentale",
            "les loisirs, le sport ou le bricolage": "loisirs_sport",
            "la culture générale": "culture_generale",
        }

        english_mapping = {
            "cooking recipes": "recipe",
            "programming and coding": "programming",
            "mathematics": "mathematics",
            "medical advice": "medical",
            "financial topics": "finance",
            "general history or geography": "history_geo",
            "general writing": "writing",
            "science and technology": "science_technology",
            "western pop culture": "western_pop_culture",
            "hobbies, sports, or DIY": "hobbies_sports",
            "general knowledge or trivial facts": "general_knowledge",
        }

        for item in refusals:
            out = item["output"]
            lang = item["language"]
            if lang == "Français":
                for phrase, cat in french_mapping.items():
                    if phrase in out:
                        french_topics_found.add(cat)
            elif lang == "English":
                for phrase, cat in english_mapping.items():
                    if phrase in out:
                        english_topics_found.add(cat)

        self.assertEqual(
            len(french_topics_found),
            11,
            f"Missing French refusal categories: {set(french_mapping.values()) - french_topics_found}",
        )
        self.assertEqual(
            len(english_topics_found),
            11,
            f"Missing English refusal categories: {set(english_mapping.values()) - english_topics_found}",
        )

    def test_run_generate_instruction_dataset_contains_refusals(self):
        import json  # noqa: E402

        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            OUTPUT_DATASET,
        )

        if os.path.exists(OUTPUT_DATASET):
            refusal_found = False
            with open(OUTPUT_DATASET, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    if "turns" not in item:
                        out_lower = item.get("output", "").lower()
                        if (
                            "animetix" in out_lower
                            and ("expertise" in out_lower or "expert" in out_lower)
                            and ("ne peux" in out_lower or "cannot" in out_lower)
                        ):
                            refusal_found = True
                            break
            self.assertTrue(
                refusal_found, "Compilation did not produce refusal negative examples"
            )

    def test_thematic_rebalancing_boosting(self):
        # We verify that underrepresented genres get boosted variation counts
        underrepresented_keywords = [
            "shoujo",
            "shojo",
            "josei",
            "slice of life",
            "tranche de vie",
            "iyashikei",
            "mecha",
            "mahou shoujo",
            "magical girl",
            "music",
            "sports",
            "historical",
            "horror",
            "thriller",
        ]

        # Mock entries
        shoujo_manga = {
            "title": "Ao Haru Ride",
            "genres": ["Romance", "Shoujo"],
            "tags": ["School Life"],
            "popularity": 10000,
        }
        shonen_manga = {
            "title": "Naruto",
            "genres": ["Action", "Shonen"],
            "tags": ["Ninja"],
            "popularity": 10000,
        }
        retro_manga = {
            "title": "Akira",
            "genres": ["Sci-Fi"],
            "tags": ["Cyberpunk"],
            "year": 1982,
            "popularity": 10000,
        }

        def get_effective_pop(item):
            pop = item.get("popularity", 0)
            genres = [g.lower() for g in item.get("genres", [])]
            tags = [t.lower() for t in item.get("tags", [])]
            year = item.get("year")

            is_underrepresented = False
            for term in underrepresented_keywords:
                if any(term in str(g) for g in genres + tags):
                    is_underrepresented = True
                    break

            if not is_underrepresented and year and 1970 <= year <= 1999:
                is_underrepresented = True

            if is_underrepresented:
                return max(pop, 150001) if pop > 50000 else 100000
            return pop

        self.assertEqual(get_effective_pop(shonen_manga), 10000)  # Standard pop
        self.assertEqual(
            get_effective_pop(shoujo_manga), 100000
        )  # Boosted to Tier 2 (100k)
        self.assertEqual(get_effective_pop(retro_manga), 100000)  # Boosted retro work

    def test_run_generate_instruction_dataset_rebalanced_ratio(self):
        import json  # noqa: E402

        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            OUTPUT_DATASET,
        )

        if os.path.exists(OUTPUT_DATASET):
            underrepresented_count = 0
            total_count = 0
            keywords = [
                "shoujo",
                "shojo",
                "josei",
                "slice of life",
                "tranche de vie",
                "iyashikei",
                "mecha",
                "mahou shoujo",
                "magical girl",
                "music",
                "sports",
                "historical",
                "horror",
                "thriller",
            ]
            with open(OUTPUT_DATASET, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    total_count += 1
                    item_str = str(item).lower()
                    if any(kw in item_str for kw in keywords):
                        underrepresented_count += 1
            ratio = (underrepresented_count / total_count) * 100
            # Confirm ratio has increased from original ~7.4% to a minimum of 10%
            self.assertGreaterEqual(
                ratio,
                10.0,
                f"Underrepresented genres representation is too low: {ratio:.2f}%",
            )

    def test_validate_factual_alignment_success(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            validate_factual_alignment,
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"aligned": true, "reason": ""}'
        mock_client.models.generate_content.return_value = mock_response

        orig = "L'anime Naruto est sorti en 2002."
        gen = "En 2002 est sorti l'anime Naruto."
        self.assertTrue(validate_factual_alignment(orig, gen, mock_client))
        mock_client.models.generate_content.assert_called_once()

    def test_validate_factual_alignment_failure(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            validate_factual_alignment,
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            '```json\n{"aligned": false, "reason": "Changement de date"}\n```'
        )
        mock_client.models.generate_content.return_value = mock_response

        orig = "L'anime Naruto est sorti en 2002."
        gen = "L'anime Naruto est sorti en 2005."
        self.assertFalse(validate_factual_alignment(orig, gen, mock_client))
        mock_client.models.generate_content.assert_called_once()

    def test_inject_query_noise(self):
        import random  # noqa: E402

        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            inject_query_noise,
        )

        random.seed(42)  # Deterministic for reproducibility

        # Test French abbreviation replacement
        text_fr = "S'il te plaît, pourquoi cet anime est un chef-d'œuvre ?"
        noisy_fr = inject_query_noise(text_fr, "Français")
        # At least one abbreviation should be applied (stp, pq, anim, masterclass)
        self.assertTrue(
            any(x in noisy_fr.lower() for x in ["stp", "pq", "anim", "masterclass"]),
            f"Expected French abbreviations in: {noisy_fr}",
        )

        # Test English abbreviation replacement
        random.seed(42)
        text_en = "What is your favorite character and are you sure about it?"
        noisy_en = inject_query_noise(text_en, "English")
        # At least one abbreviation should be applied (wht, fav, char, r, u, abt)
        self.assertTrue(
            any(x in noisy_en.lower() for x in ["wht", "fav", "char", "r", "u", "abt"]),
            f"Expected English abbreviations in: {noisy_en}",
        )

        # Verify that the noisy text is different from the original
        random.seed(42)
        self.assertNotEqual(
            inject_query_noise(
                "Bonjour, pourquoi cet anime est populaire ?", "Français"
            ),
            "Bonjour, pourquoi cet anime est populaire ?",
        )

        # Verify empty text returns empty
        self.assertEqual(inject_query_noise("", "Français"), "")

    def test_generate_rag_context_instructions(self):
        from backend.pipeline.mlops.finetuning_dataset import (  # noqa: E402
            generate_rag_context_instructions,
        )

        animes = [
            {
                "title": "Naruto",
                "genres": ["Action"],
                "studios": ["Pierrot"],
                "year": 2002,
            }
        ]
        chars = [
            {
                "name": "Luffy",
                "origin": "One Piece",
                "popularity": {"favourites": 150000},
                "metadata": {"height": "174cm"},
            }
        ]

        instructions = generate_rag_context_instructions(animes, chars)
        self.assertGreater(len(instructions), 0)
        for item in instructions:
            self.assertIn("instruction", item)
            self.assertIn("input", item)
            self.assertIn("output", item)
            # Verify input contains document markers
            self.assertTrue("[" in item["input"] and "]" in item["input"])
            # Verify output mentions ignoring or Document/Source
            self.assertTrue(
                "Document" in item["output"]
                or "Source" in item["output"]
                or "ignor" in item["output"].lower()
            )


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
        {
            "instruction": f"{tag}-{i}",
            "input": "",
            "output": "o",
            "language": "Français",
        }
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
            _tag = gen.removeprefix("generate_").removesuffix("_instructions")
            patch_attr(
                gen, MagicMock(side_effect=lambda *a, _g=_tag, **k: _items(_g, 2))
            )
        patch_attr("generate_rag_context_instructions", _fixed(_items("rag", 2)))
        patch_attr("generate_otaku_meta_instructions", _fixed(_items("meta", 3)))
        patch_attr("generate_negative_refusal_examples", _fixed(_items("refusal", 2)))
        patch_attr(
            "generate_multiturn_dialogues",
            _fixed(
                [
                    {
                        "turns": [{"user": "u", "assistant": "a"}],
                        "language": "Français",
                    },
                    {
                        "turns": [{"user": "u2", "assistant": "a2"}],
                        "language": "English",
                    },
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
        self.assertTrue(
            any(instr(it).startswith("awards_and_magazines") for it in data)
        )
        self.assertTrue(any(instr(it).startswith("songs_and_seiyuu") for it in data))
        self.assertTrue(
            any(instr(it).startswith("french_market_relations") for it in data)
        )
        self.assertTrue(
            any(instr(it).startswith("japanese_market_relations") for it in data)
        )
        self.assertTrue(
            any(instr(it).startswith("french_market_profile") for it in data)
        )
        self.assertTrue(
            any(instr(it).startswith("japanese_market_profile") for it in data)
        )
        self.assertTrue(
            any(instr(it).startswith("volumes_and_episodes") for it in data)
        )
        self.assertTrue(any(instr(it).startswith("mcp_tool") for it in data))
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


if __name__ == "__main__":
    unittest.main()
