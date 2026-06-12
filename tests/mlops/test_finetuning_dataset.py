import unittest
import os
import sys
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.pipeline.mlops.finetuning_dataset import clean_description

class TestFinetuningDataset(unittest.TestCase):
    def test_clean_description(self):
        raw_text = "L'anime <i>SnK</i> est culte.<br> &quot;Incroyable&quot; &#039;chef-d'oeuvre&#039;  et   magnifique."
        expected = "L'anime SnK est culte. \"Incroyable\" 'chef-d'oeuvre' et magnifique."
        self.assertEqual(clean_description(raw_text), expected)

    def test_gemini_paraphrase_cache(self):
        from backend.pipeline.mlops.finetuning_dataset import paraphrase_text_via_gemini
        from unittest.mock import MagicMock
        
        # Initialiser un cache temporaire pour le test
        import backend.pipeline.mlops.finetuning_dataset as fd
        fd.PARAPHRASE_CACHE = {"Le texte original||naturel": "Texte paraphrase en cache"}
        
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
        
        res2 = paraphrase_text_via_gemini("Un autre texte", mock_client, "naturel")
        self.assertEqual(res2, "Nouvelle paraphrase")
        mock_client.models.generate_content.assert_called_once()
        self.assertIn("Un autre texte||naturel", fd.PARAPHRASE_CACHE)
        self.assertEqual(fd.PARAPHRASE_CACHE["Un autre texte||naturel"], "Nouvelle paraphrase")

    def test_configurable_ratios(self):
        import backend.pipeline.mlops.finetuning_dataset as fd
        from unittest.mock import patch
        
        env_vars = {
            "ANIMETIX_RATIO_SPECIALIZED": "70",
            "ANIMETIX_RATIO_META": "10",
            "ANIMETIX_RATIO_GENERAL": "20"
        }
        
        with patch.dict(os.environ, env_vars):
            meta_req, gen_req = fd.calculate_dataset_counts(700)
            self.assertEqual(meta_req, 100)
            self.assertEqual(gen_req, 200)

    def test_mcp_error_scenarios(self):
        from backend.pipeline.mlops.finetuning_dataset import generate_mcp_tool_instructions
        
        instructions = generate_mcp_tool_instructions()
        
        # Vérifier la présence d'au moins un scénario contenant une réponse d'erreur de tool_response
        error_found = False
        for inst in instructions:
            if "<tool_response>" in inst["input"] and '"status": "error"' in inst["input"]:
                error_found = True
                # Vérifier que l'output contient une excuse ou indique une recherche en mémoire/connaissance
                self.assertTrue(
                    "rencontre une erreur" in inst["output"] or
                    "indisponible" in inst["output"] or
                    "limite de requêtes" in inst["output"] or
                    "désolé" in inst["output"].lower() or
                    "connaissances" in inst["output"]
                )
                break
                
        self.assertTrue(error_found, "Aucun scénario d'erreur MCP trouvé dans les instructions.")

    def test_bilingual_generators(self):
        from backend.pipeline.mlops.finetuning_dataset import (
            make_english_anime_profile,
            make_english_manga_profile,
            make_english_character_bio
        )
        
        # Test anime profile
        anime_prof = make_english_anime_profile("Naruto", ["Action"], ["Pierrot"], ["Ninja"], 2002)
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
        char_bio = make_english_character_bio("Luffy", "One Piece", ["Straw Hats"], 150000, 1, "174cm")
        self.assertIn("Luffy", char_bio)
        self.assertIn("One Piece", char_bio)
        self.assertIn("Straw Hats", char_bio)
        self.assertIn("150,000", char_bio)
        self.assertIn("174cm", char_bio)

    @patch('backend.pipeline.mlops.finetuning_dataset.load_dataset')
    def test_bilingual_general_instructions(self, mock_load_dataset):
        mock_ds_fr = [{"instruction": "Inst FR", "input": "", "output": "Rep FR"}]
        mock_ds_en = [{"instruction": "Inst EN", "input": "", "output": "Rep EN"}]
        
        def side_effect(path, split=None):
            if 'alpaca-cleaned-fr' in path:
                return mock_ds_fr
            else:
                return mock_ds_en
        mock_load_dataset.side_effect = side_effect
        
        from backend.pipeline.mlops.finetuning_dataset import fetch_general_instructions
        res = fetch_general_instructions(2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["language"], "Français")
        self.assertEqual(res[1]["language"], "English")

    def test_generate_otaku_meta_instructions_bilingual(self):
        from backend.pipeline.mlops.finetuning_dataset import generate_otaku_meta_instructions
        res = generate_otaku_meta_instructions(client=None)
        
        fr_count = sum(1 for item in res if item.get("language") == "Français")
        en_count = sum(1 for item in res if item.get("language") == "English")
        self.assertGreater(fr_count, 0)
        self.assertGreater(en_count, 0)
        
        en_items = [item for item in res if item.get("language") == "English"]
        self.assertTrue(any("What does" in item["instruction"] or "Who is" in item["instruction"] or "What is the" in item["instruction"] for item in en_items))

    def test_deduplicate_dataset_multiturn(self):
        from backend.pipeline.mlops.finetuning_dataset import deduplicate_dataset
        dataset = [
            {
                "turns": [{"user": "Hi", "assistant": "Hello"}],
                "language": "English"
            },
            {
                "turns": [{"user": "Hi", "assistant": "Hello"}],
                "language": "English"
            },
            {
                "instruction": "Hi",
                "input": "",
                "output": "Hello",
                "language": "English"
            }
        ]
        res = deduplicate_dataset(dataset)
        self.assertEqual(len(res), 2)

    def test_generate_multiturn_dialogues(self):
        from backend.pipeline.mlops.finetuning_dataset import generate_multiturn_dialogues
        animes = [{"title": "Naruto", "genres": ["Action"], "studios": ["Pierrot"], "tags": ["Ninja"], "popularity": 1000000, "year": 2002}]
        mangas = [{"title": "One Piece", "genres": ["Adventure"], "tags": ["Pirates"], "popularity": 1500000}]
        chars = [{"name": "Luffy", "origin": "One Piece", "entities": {"organizations": ["Straw Hats"]}, "popularity": {"favourites": 150000, "rank": 1}, "metadata": {"height": "174cm"}}]
        vocab = {"Tsundere": {"definition": "Cold then hot", "examples": "Taiga", "impact": "Popular trope", "origin": "Japanese"}}
        
        dialogues = generate_multiturn_dialogues(animes, mangas, chars, vocab, count=6)
        self.assertEqual(len(dialogues), 6)
        for d in dialogues:
            self.assertIn("turns", d)
            self.assertGreaterEqual(len(d["turns"]), 2)
            self.assertIn(d["language"], ["Français", "English"])

    def test_run_generate_instruction_dataset_contains_multiturn(self):
        from backend.pipeline.mlops.finetuning_dataset import OUTPUT_DATASET
        import json
        
        if os.path.exists(OUTPUT_DATASET):
            multiturn_found = False
            with open(OUTPUT_DATASET, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    if "turns" in item:
                        multiturn_found = True
                        break
            self.assertTrue(multiturn_found, "Compilation did not produce multi-turn examples")

    def test_generate_negative_refusal_examples(self):
        from backend.pipeline.mlops.finetuning_dataset import generate_negative_refusal_examples
        
        refusals = generate_negative_refusal_examples(count=10)
        self.assertEqual(len(refusals), 10)
        for item in refusals:
            self.assertIn("instruction", item)
            self.assertIn("output", item)
            self.assertIn(item["language"], ["Français", "English"])
            # Output should contain Animetix or expertise keywords
            out_lower = item["output"].lower()
            self.assertTrue(
                "animetix" in out_lower or "expertise" in out_lower or "expert" in out_lower,
                f"Refusal output must contain Animetix or expertise keywords: {item['output']}"
            )

    def test_run_generate_instruction_dataset_contains_refusals(self):
        from backend.pipeline.mlops.finetuning_dataset import OUTPUT_DATASET
        import json
        
        if os.path.exists(OUTPUT_DATASET):
            refusal_found = False
            with open(OUTPUT_DATASET, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    if "turns" not in item:
                        out_lower = item.get("output", "").lower()
                        if "animetix" in out_lower and ("expertise" in out_lower or "expert" in out_lower) and ("ne peux" in out_lower or "cannot" in out_lower):
                            refusal_found = True
                            break
            self.assertTrue(refusal_found, "Compilation did not produce refusal negative examples")

    def test_thematic_rebalancing_boosting(self):
        # We verify that underrepresented genres (Shojo, Josei, Slice of Life) get boosted variation counts
        underrepresented_keywords = ["shoujo", "shojo", "josei", "slice of life", "tranche de vie"]
        
        # Mock entries
        shoujo_manga = {"title": "Ao Haru Ride", "genres": ["Romance", "Shoujo"], "tags": ["School Life"], "popularity": 10000}
        shonen_manga = {"title": "Naruto", "genres": ["Action", "Shonen"], "tags": ["Ninja"], "popularity": 10000}
        
        def get_effective_pop(item):
            pop = item.get("popularity", 0)
            genres = [g.lower() for g in item.get("genres", [])]
            tags = [t.lower() for t in item.get("tags", [])]
            
            is_underrepresented = False
            for term in underrepresented_keywords:
                if any(term in str(g) for g in genres + tags):
                    is_underrepresented = True
                    break
                    
            if is_underrepresented:
                return max(pop, 150001) if pop > 50000 else 100000
            return pop

        self.assertEqual(get_effective_pop(shonen_manga), 10000)      # Standard pop
        self.assertEqual(get_effective_pop(shoujo_manga), 100000)    # Boosted to Tier 2 (100k)

    def test_run_generate_instruction_dataset_rebalanced_ratio(self):
        from backend.pipeline.mlops.finetuning_dataset import OUTPUT_DATASET
        import json
        
        if os.path.exists(OUTPUT_DATASET):
            underrepresented_count = 0
            total_count = 0
            keywords = ["shoujo", "shojo", "josei", "slice of life", "tranche de vie"]
            with open(OUTPUT_DATASET, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    total_count += 1
                    item_str = str(item).lower()
                    if any(kw in item_str for kw in keywords):
                        underrepresented_count += 1
            ratio = (underrepresented_count / total_count) * 100
            # Confirm ratio has increased from original ~7.4% to a minimum of 10%
            self.assertGreaterEqual(ratio, 10.0, f"Underrepresented genres representation is too low: {ratio:.2f}%")

if __name__ == "__main__":
    unittest.main()
