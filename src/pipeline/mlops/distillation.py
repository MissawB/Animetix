import os
import sys

# Ajout du chemin src pour l'import des scripts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'scripts'))

from distill_draft_model import train_speculative_draft_model

def run_distillation():
    """
    Lance le pipeline de distillation pour créer le Draft Model.
    Utilisé pour le Speculative Decoding dans LocalLlamaAdapter.
    """
    print("💎 Starting Speculative Decoding Distillation...")
    
    # Configuration par défaut
    teacher = "meta-llama/Llama-3-8B-Instruct" # Ou un modèle local si dispo
    student = "HuggingFaceTB/SmolLM-135M"
    output = os.path.join(BASE_DIR, "checkpoints", "animetix-draft-135m")
    
    try:
        # On utilise une valeur d'epochs faible pour le pipeline par défaut (ex: 1.0)
        # Mais on assure que c'est le REEL entraînement qui est lancé.
        train_speculative_draft_model(
            teacher_model_id=teacher,
            student_model_id=student,
            output_dir=output,
            epochs=1.0
        )
        print("✅ Real Distillation Pipeline Complete.")
        return output
    except Exception as e:
        print(f"❌ Distillation Failed: {e}")
        return None

if __name__ == "__main__":
    run_distillation()
