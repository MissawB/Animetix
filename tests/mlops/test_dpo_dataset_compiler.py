# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import json
import random

class TestDPODatasetCompiler(unittest.TestCase):
    def setUp(self):
        # We dynamic import to allow tests to load after implementation exists
        pass

    def test_corrupt_fact_substitution(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_fact_substitution
        
        # Test years/numbers substitution (fallback)
        text_num = "Cet anime est sorti en 2018 avec 24 épisodes."
        corr_num = corrupt_fact_substitution(text_num, "Français")
        self.assertNotEqual(text_num, corr_num)
        self.assertTrue(any(str(year) in corr_num for year in range(1980, 2027) if str(year) != "2018"))

        # Test studio close-concept replacement
        text_studio = "L'anime a été produit par Wit Studio."
        corr_studio = corrupt_fact_substitution(text_studio, "Français")
        self.assertNotEqual(text_studio, corr_studio)
        
        text_ufotable = "L'anime a été produit par ufotable."
        corr_ufo = corrupt_fact_substitution(text_ufotable, "Français")
        self.assertNotEqual(text_ufotable, corr_ufo)
        self.assertTrue(any(s in corr_ufo for s in ["MAPPA", "Studio Trigger", "Bones", "Sunrise", "Wit Studio", "Studio Ghibli", "Kyoto Animation", "Madhouse", "Studio Pierrot"]))

        # Test voice actor franchise replacement
        text_va = "Son Goku est doublé par Brigitte Lecordier."
        corr_va = corrupt_fact_substitution(text_va, "Français")
        self.assertNotEqual(text_va, corr_va)
        self.assertTrue(any(v in corr_va for v in ["Patrick Borg", "Eric Legrand", "Philippe Ariotti"]))

        # Test publisher group replacement
        text_pub = "Le manga est édité par Glénat Manga."
        corr_pub = corrupt_fact_substitution(text_pub, "Français")
        self.assertNotEqual(text_pub, corr_pub)
        self.assertTrue(any(p in corr_pub for p in ["Kana", "Pika Édition", "Kurokawa", "Ki-oon", "Crunchyroll Manga"]))

    def test_corrupt_tonal_deviation(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_tonal_deviation
        
        text = "Cet anime est un chef-d'œuvre avec d'excellents personnages. C'est incroyable !"
        
        strategies_seen = {
            "code_switching": False,
            "redundancy": False,
            "condescending": False
        }
        
        for _ in range(50):
            corr = corrupt_tonal_deviation(text, "Français")
            # 1. Code-switching check
            if "masterpiece" in corr or "character" in corr or "basically" in corr.lower():
                strategies_seen["code_switching"] = True
            # 2. Redundancy check
            if "préciser" in corr or "explication" in corr or "répète" in corr.lower():
                strategies_seen["redundancy"] = True
            # 3. Condescending check
            if "évident" in corr or "otaku" in corr or "Franchement" in corr or "triviale" in corr:
                strategies_seen["condescending"] = True
                
        self.assertTrue(strategies_seen["code_switching"], "Code-switching strategy was not triggered")
        self.assertTrue(strategies_seen["redundancy"], "Redundancy strategy was not triggered")
        self.assertTrue(strategies_seen["condescending"], "Condescending strategy was not triggered")

    def test_corrupt_abrupt_truncation(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_abrupt_truncation
        
        text = "C'est un long texte informatif sur la japanimation avec beaucoup de détails techniques sur les doubleurs français."
        corr = corrupt_abrupt_truncation(text)
        
        self.assertTrue(len(corr) < len(text))
        self.assertTrue(len(corr) >= len(text) * 0.25)  # Safe bounds
        # Should not end with clean sentence completion punctuation
        self.assertFalse(corr.endswith("."))

    def test_corrupt_evasive_refusal(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import corrupt_evasive_refusal
        
        text = "Voici les informations complètes sur Sword Art Online."
        
        corr_fr = corrupt_evasive_refusal(text, "Français")
        self.assertTrue(any(x in corr_fr.lower() for x in ["désolé", "aucune idée"]))
        
        corr_en = corrupt_evasive_refusal(text, "English")
        self.assertTrue(any(x in corr_en.lower() for x in ["sorry", "don't know"]))

    def test_compile_dpo_pairs(self):
        from backend.pipeline.mlops.dpo_dataset_compiler import compile_dpo_pairs
        
        # Setup mock SFT dataset
        mock_data = [
            # 1. Valid entry (long enough)
            {"instruction": "Explique l'importance de Wit Studio.", "input": "", "output": "Wit Studio est un studio d'animation japonais de premier plan fondé en juin 2012 par des producteurs de Production I.G.", "language": "Français"},
            # 2. Too short (should be filtered out)
            {"instruction": "Qui est Luffy ?", "input": "", "output": "Le héros de One Piece.", "language": "Français"},
            # 3. Refusal (should be filtered out)
            {"instruction": "Donne moi des leaks.", "input": "", "output": "Désolé, je ne dispose pas d'informations sur des rumeurs ou leaks non confirmés.", "language": "Français"},
            # 4. Another valid entry
            {"instruction": "What is the release year of Death Note?", "input": "", "output": "The anime adaptation of Death Note was produced by Madhouse and aired in Japan in 2006.", "language": "English"},
            # 5. Third valid entry
            {"instruction": "Parle moi de My Hero Academia.", "input": "", "output": "My Hero Academia est un manga shonen écrit et dessiné par Kohei Horikoshi depuis 2014.", "language": "Français"},
            # 6. Fourth valid entry
            {"instruction": "Qui est Gojo Satoru ?", "input": "", "output": "Gojo Satoru est le puissant mentor dans le manga Jujutsu Kaisen créé par Gege Akutami.", "language": "Français"}
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

if __name__ == "__main__":
    unittest.main()
