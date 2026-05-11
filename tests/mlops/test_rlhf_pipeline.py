import pytest
import os
import json
from pipeline.mlops.rlhf_pipeline import trl_ready_dataset
from dagster import build_asset_context

def test_trl_ready_dataset_transformation(tmp_path):
    """Vérifie que l'asset Dagster transforme correctement les fichiers JSONL."""
    
    # 1. Créer des données simulées d'export (JSONL)
    feedback_file = tmp_path / "ai_feedback.jsonl"
    session_file = tmp_path / "gameplay_sessions.jsonl"
    
    # Feedback positif
    feedback_file.write_text(json.dumps({
        "context": "Fusion Goku et Luffy",
        "output": "Une fusion épique avec un chapeau de paille et des cheveux jaunes.",
        "is_positive": True
    }) + "\n")
    
    # Feedback négatif
    feedback_file.write_text(feedback_file.read_text() + json.dumps({
        "context": "Qui est Ichigo ?",
        "output": "C'est un ninja de Konoha.", # Fausse info
        "is_positive": False
    }) + "\n")
    
    # Session de jeu gagnée
    session_file.write_text(json.dumps({
        "game_mode": "akinetix",
        "media_type": "anime",
        "target": "Zoro",
        "history": [{"q": "Épéiste ?", "a": "Oui"}],
        "was_won": True
    }) + "\n")

    # 2. Configurer le contexte et les entrées pour Dagster
    exported_data = {
        "feedback": str(feedback_file),
        "sessions": str(session_file)
    }
    
    # Rediriger temporairement le dossier de sortie
    output_dir = tmp_path / "mlops" / "datasets"
    os.makedirs(output_dir, exist_ok=True)
    
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("pipeline.mlops.rlhf_pipeline.FEEDBACK_DATASET_DIR", str(output_dir))
        
        # 3. Exécuter la fonction de l'asset
        dataset_path = trl_ready_dataset(exported_data)
        
        # 4. Vérifier le résultat
        assert os.path.exists(dataset_path)
        with open(dataset_path, 'r', encoding='utf-8') as f:
            lines = [json.loads(line) for line in f]
            
            # On attend 3 entrées (1 pos, 1 neg, 1 session)
            assert len(lines) == 3
            
            # Vérifier le format DPO (prompt/chosen/rejected)
            assert "prompt" in lines[0]
            assert "chosen" in lines[0]
            assert "rejected" in lines[0]
            
            # Vérifier la déduction logique de la session
            session_entry = lines[2]
            assert "Zoro" in session_entry["chosen"]
            assert "Épéiste" in session_entry["prompt"]
