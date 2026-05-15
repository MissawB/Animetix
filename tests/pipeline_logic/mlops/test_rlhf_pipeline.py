import pytest
import os
import json
from pipeline.mlops.rlhf_pipeline import validated_dpo_dataset
from dagster import build_asset_context

def test_validated_dpo_dataset_transformation(tmp_path):
    """Vérifie que l'asset Dagster transforme correctement les fichiers JSONL."""
    
    # 1. Créer des données simulées d'export (JSONL)
    feedback_file = tmp_path / "ai_feedback.jsonl"
    session_file = tmp_path / "gameplay_sessions.jsonl"
    
    # Feedback positif
    feedback_file.write_text(json.dumps({
        "input_context": "Fusion Goku et Luffy",
        "output_text": "Une fusion épique avec un chapeau de paille et des cheveux jaunes.",
        "is_positive": True
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
        result = validated_dpo_dataset(exported_data)
        dataset_path = result["path"]
        
        # 4. Vérifier le résultat
        assert os.path.exists(dataset_path)
