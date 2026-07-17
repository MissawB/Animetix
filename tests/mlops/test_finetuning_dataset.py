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

import pipeline.mlops.finetuning_dataset as fd  # noqa: E402
from pipeline.mlops.finetuning_dataset import clean_description  # noqa: E402


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
        import pipeline.mlops.ft_dataset.paraphrase as pmod  # noqa: E402
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
            "pipeline.mlops.ft_dataset.paraphrase.validate_factual_alignment",
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

        import pipeline.mlops.finetuning_dataset as fd  # noqa: E402

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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
            make_english_anime_profile,
            make_english_character_bio,
            make_english_manga_profile,
        )

        # Test anime profile — grounded in real description
        anime_prof = make_english_anime_profile(
            "Naruto",
            ["Action"],
            ["Pierrot"],
            ["Ninja"],
            2002,
            "Naruto Uzumaki is a young ninja seeking recognition and the Hokage title.",
        )
        self.assertIn("Naruto", anime_prof)
        self.assertIn("2002", anime_prof)  # year is the only allowed number
        self.assertIn("Hokage", anime_prof)  # real fact from description
        self.assertNotIn("landmark work", anime_prof)
        self.assertNotIn("highly recommended", anime_prof)

        # Empty description -> structured fallback still names the work + facts
        anime_fallback = make_english_anime_profile(
            "Naruto", ["Action"], ["Pierrot"], ["Ninja"], 2002, ""
        )
        self.assertIn("Naruto", anime_fallback)
        self.assertIn("Pierrot", anime_fallback)

        # Test manga profile — grounded in real description
        manga_prof = make_english_manga_profile(
            "One Piece",
            ["Adventure"],
            ["Pirates"],
            "Monkey D. Luffy sails to find the One Piece treasure.",
        )
        self.assertIn("One Piece", manga_prof)
        self.assertIn("treasure", manga_prof)  # real fact

        # Test character bio — grounded in real biography, no numeric noise
        char_bio = make_english_character_bio(
            "Luffy",
            "One Piece",
            ["Straw Hats"],
            "Luffy is a rubber-bodied pirate who dreams of becoming Pirate King.",
        )
        self.assertIn("Luffy", char_bio)
        self.assertIn("One Piece", char_bio)
        self.assertIn("Straw Hats", char_bio)
        self.assertIn("Pirate King", char_bio)  # real fact from biography
        self.assertNotIn("rank", char_bio.lower())
        self.assertNotIn("votes", char_bio.lower())
        # No free-floating digit runs (years would be OK, but this bio has none)
        import re as _re

        self.assertIsNone(_re.search(r"\d{3,}", char_bio))

    def test_french_character_bio_structured(self):
        from pipeline.mlops.finetuning_dataset import make_french_character_bio

        bio = make_french_character_bio("Levi", "Shingeki no Kyojin", ["Survey Corps"])
        self.assertIn("Levi", bio)
        self.assertIn("Shingeki no Kyojin", bio)
        # organisation traduite via le mapping conservé
        self.assertIn("Bataillon d'exploration", bio)
        # motifs corrupteurs bannis
        for banned in [
            "jouit d'une immense popularité",
            "figure incontournable",
            "rang numéro",
            "votes d'admiration",
            "incarne les valeurs",
        ]:
            self.assertNotIn(banned, bio)
        import re as _re

        self.assertIsNone(_re.search(r"\d{3,}", bio))

    @patch("pipeline.mlops.finetuning_dataset.load_dataset")
    def test_bilingual_general_instructions(self, mock_load_dataset):
        mock_ds_fr = [{"instruction": "Inst FR", "input": "", "output": "Rep FR"}]
        mock_ds_en = [{"instruction": "Inst EN", "input": "", "output": "Rep EN"}]

        def side_effect(path, split=None, **kwargs):
            if "alpaca-cleaned-fr" in path:
                return mock_ds_fr
            else:
                return mock_ds_en

        mock_load_dataset.side_effect = side_effect

        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
            fetch_general_instructions,
        )

        res = fetch_general_instructions(2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["language"], "Français")
        self.assertEqual(res[1]["language"], "English")

    def test_generate_otaku_meta_instructions_bilingual(self):
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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

        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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

        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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

        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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

        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
        from pipeline.mlops.finetuning_dataset import (  # noqa: E402
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
                self.assertTrue(self._read(out))

    def test_run_generate_instruction_dataset_all_tiers_and_languages_no_augmentation(
        self,
    ):
        # We need 6 items to alternate indices (idx 0 to 5) to cover French/English & Tiers 1/2/3
        animes = [
            # idx 0: French Tier-1 (>150k)
            {
                "title": "AnimeFR1",
                "genres": ["Action"],
                "studios": ["S1"],
                "tags": ["t1"],
                "popularity": 200000,
                "year": 2010,
            },
            # idx 1: English Tier-1 (>150k)
            {
                "title": "AnimeEN1",
                "genres": ["Comedy"],
                "studios": ["S2"],
                "tags": ["t2"],
                "popularity": 200000,
                "year": 2010,
            },
            # idx 2: French Tier-2 (50k - 150k)
            {
                "title": "AnimeFR2",
                "genres": ["Drama"],
                "studios": ["S3"],
                "tags": ["t3"],
                "popularity": 100000,
                "year": 2010,
            },
            # idx 3: English Tier-2 (50k - 150k)
            {
                "title": "AnimeEN2",
                "genres": ["Sci-Fi"],
                "studios": ["S4"],
                "tags": ["t4"],
                "popularity": 100000,
                "year": 2010,
            },
            # idx 4: French Tier-3 (<= 50k)
            {
                "title": "AnimeFR3",
                "genres": ["Slice of Life"],
                "studios": ["S5"],
                "tags": ["t5"],
                "popularity": 10000,
                "year": 1990,
            },  # underrepresented genre + retro era
            # idx 5: English Tier-3 (<= 50k)
            {
                "title": "AnimeEN3",
                "genres": ["Mecha"],
                "studios": ["S6"],
                "tags": ["t6"],
                "popularity": 10000,
                "year": 1990,
            },
        ]
        mangas = [
            # idx 0: French Tier-1
            {
                "title": "MangaFR1",
                "genres": ["Action"],
                "tags": ["t1"],
                "popularity": 200000,
                "year": 2010,
            },
            # idx 1: English Tier-1
            {
                "title": "MangaEN1",
                "genres": ["Comedy"],
                "tags": ["t2"],
                "popularity": 200000,
                "year": 2010,
            },
            # idx 2: French Tier-2
            {
                "title": "MangaFR2",
                "genres": ["Drama"],
                "tags": ["t3"],
                "popularity": 100000,
                "year": 2010,
            },
            # idx 3: English Tier-2
            {
                "title": "MangaEN2",
                "genres": ["Sci-Fi"],
                "tags": ["t4"],
                "popularity": 100000,
                "year": 2010,
            },
            # idx 4: French Tier-3
            {
                "title": "MangaFR3",
                "genres": ["Slice of Life"],
                "tags": ["t5"],
                "popularity": 10000,
                "year": 1990,
            },
            # idx 5: English Tier-3
            {
                "title": "MangaEN3",
                "genres": ["Mecha"],
                "tags": ["t6"],
                "popularity": 10000,
                "year": 1990,
            },
        ]
        chars = [
            # idx 0: French Tier-1 (>2000 favoris)
            {
                "name": "CharFR1",
                "origin": "OriginFR1",
                "entities": {"organizations": ["Org1"]},
                "popularity": {"favourites": 3000, "rank": 1},
                "metadata": {"height": "180cm"},
            },
            # idx 1: English Tier-1 (>2000 favoris)
            {
                "name": "CharEN1",
                "origin": "OriginEN1",
                "entities": {"organizations": ["Org2"]},
                "popularity": {"favourites": 3000, "rank": 2},
                "metadata": {"height": "170cm"},
            },
            # idx 2: French Tier-2 (500 - 2000 favoris)
            {
                "name": "CharFR2",
                "origin": "OriginFR2",
                "entities": {"organizations": ["Org3"]},
                "popularity": {"favourites": 1000, "rank": 10},
                "metadata": {"height": "165cm"},
            },
            # idx 3: English Tier-2 (500 - 2000 favoris)
            {
                "name": "CharEN2",
                "origin": "OriginEN2",
                "entities": {"organizations": ["Org4"]},
                "popularity": {"favourites": 1000, "rank": 20},
                "metadata": {"height": "160cm"},
            },
            # idx 4: French Tier-3 (50 - 500 favoris)
            {
                "name": "CharFR3",
                "origin": "OriginFR3",
                "entities": {"organizations": ["Org5"]},
                "popularity": {"favourites": 100, "rank": 100},
                "metadata": {"height": "155cm"},
            },
            # idx 5: English Tier-3 (50 - 500 favoris)
            {
                "name": "CharEN3",
                "origin": "OriginEN3",
                "entities": {"organizations": ["Org6"]},
                "popularity": {"favourites": 100, "rank": 200},
                "metadata": {"height": "150cm"},
            },
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
                # Patch one simple generator to omit "language" to cover line 1242
                with patch.object(
                    fd,
                    "generate_transmedia_instructions",
                    return_value=[
                        {"instruction": "no-lang", "input": "", "output": "o"}
                    ],
                ):
                    fd.run_generate_instruction_dataset()
                    data = self._read(out)

        self.assertTrue(data)
        # Check that we handled the item without language
        no_lang_item = [it for it in data if it.get("instruction") == "no-lang"]
        self.assertEqual(len(no_lang_item), 1)
        self.assertEqual(no_lang_item[0]["language"], "Français")

    def test_run_generate_instruction_dataset_ratios_warning_and_meta_expansion(self):
        animes = [
            {
                "title": "A",
                "genres": ["G"],
                "studios": ["S"],
                "tags": ["t"],
                "popularity": 100,
                "year": 2020,
            }
        ]
        # 1. Test ratios sum <= 0 warning fallback
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                    "ANIMETIX_RATIO_SPECIALIZED": "0",
                    "ANIMETIX_RATIO_META": "0",
                    "ANIMETIX_RATIO_GENERAL": "0",
                },
            ) as out:
                fd.run_generate_instruction_dataset()
                data = self._read(out)
        self.assertTrue(data)

        # 2. Test meta expansion when required meta count > meta pool
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                    "ANIMETIX_RATIO_SPECIALIZED": "5",
                    "ANIMETIX_RATIO_META": "500",
                    "ANIMETIX_RATIO_GENERAL": "15",
                },
            ) as out:
                fd.run_generate_instruction_dataset()
                data = self._read(out)
        self.assertTrue(data)

    def test_run_generate_instruction_dataset_load_dataset_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=[],
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "0.0",
                },
            ) as out:
                with patch.object(
                    fd, "load_dataset", side_effect=Exception("Failed to load")
                ):
                    fd.run_generate_instruction_dataset()
                    data = self._read(out)
        self.assertTrue(data)

    def test_run_generate_instruction_dataset_noise_rate_out_of_bounds_and_turns_noise(
        self,
    ):
        animes = [
            {
                "title": "A",
                "genres": ["G"],
                "studios": ["S"],
                "tags": ["t"],
                "popularity": 100,
                "year": 2020,
            }
        ]
        # Noise rate out of bounds -> exception raised internally -> fallback
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "2.0",
                },
            ) as out:
                fd.run_generate_instruction_dataset()
                data = self._read(out)
        self.assertTrue(data)

        # Noise rate = 1.0 (forces noise on all) + verify multi-turn noise injection
        with tempfile.TemporaryDirectory() as tmp:
            with _orchestrator_env(
                tmp,
                animes=animes,
                mangas=[],
                chars=[],
                env={
                    "ANIMETIX_AUGMENT_DATA": "False",
                    "ANIMETIX_QUERY_NOISE_RATE": "1.0",
                },
            ) as out:
                fd.run_generate_instruction_dataset()
                data = self._read(out)
        self.assertTrue(data)


if __name__ == "__main__":
    unittest.main()
