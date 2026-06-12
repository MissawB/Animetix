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

    def test_compile_dpo_pairs_with_db_feedback(self):
        from unittest.mock import patch, MagicMock
        from backend.pipeline.mlops.dpo_dataset_compiler import compile_dpo_pairs
        
        # Mocking fetch_db_feedbacks to simulate user feedback entries
        mock_feedbacks = [
            # 1. Thumbs up feedback (should trigger positive DPO pair generation)
            {"context": "Qui est Shinji Ikari ?", "output": "Shinji Ikari est le protagoniste de Neon Genesis Evangelion, un adolescent complexe qui pilote l'EVA-01.", "is_positive": True, "feedback_type": "thumbs_up"},
            # 2. Thumbs down feedback (should trigger Gemini Oracle chosen generation)
            {"context": "Quel studio a fait Demon Slayer ?", "output": "C'est MAPPA, non ?", "is_positive": False, "feedback_type": "thumbs_down"}
        ]
        
        with patch('backend.pipeline.mlops.dpo_feedback_loop.django_available', True), \
             patch('backend.pipeline.mlops.dpo_feedback_loop.AIFeedback') as mock_ai_feedback:
            
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
            with patch('backend.pipeline.mlops.dpo_feedback_loop.DPOFeedbackLoop.generate_oracle_response') as mock_oracle:
                mock_oracle.return_value = "Demon Slayer a été produit par le studio ufotable, connu pour son animation de haute qualité."
                
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    sft_file = os.path.join(tmpdir, "sft.jsonl")
                    output_file = os.path.join(tmpdir, "dpo.jsonl")
                    
                    # Create empty SFT file so compiler only outputs feedback pairs
                    with open(sft_file, "w", encoding="utf-8") as f:
                        pass
                        
                    compiled_count = compile_dpo_pairs(sft_file, output_file, limit=5, seed=42)
                    
                    # We expect 2 pairs compiled (both mock feedbacks validated and converted)
                    self.assertEqual(compiled_count, 2)
                    
                    with open(output_file, "r", encoding="utf-8") as f:
                        lines = [json.loads(line) for line in f]
                        
                    self.assertEqual(len(lines), 2)
                    
                    # Verify positive feedback pair
                    p1 = lines[0]
                    self.assertEqual(p1["prompt"], "Génère une réponse expert pour : Qui est Shinji Ikari ?")
                    self.assertEqual(p1["chosen"], "Shinji Ikari est le protagoniste de Neon Genesis Evangelion, un adolescent complexe qui pilote l'EVA-01.")
                    self.assertNotEqual(p1["rejected"], p1["chosen"])
                    
                    # Verify negative feedback pair
                    p2 = lines[1]
                    self.assertEqual(p2["prompt"], "Génère une réponse expert pour : Quel studio a fait Demon Slayer ?")
                    self.assertEqual(p2["chosen"], "Demon Slayer a été produit par le studio ufotable, connu pour son animation de haute qualité.")
                    self.assertEqual(p2["rejected"], "C'est MAPPA, non ?")

if __name__ == "__main__":
    unittest.main()
