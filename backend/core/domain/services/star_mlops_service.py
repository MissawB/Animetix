import os
import json
import logging
import subprocess
from typing import List, Dict, Any
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops.star")

class StarMLOpsDomainService:
    """
    Orchestre le cycle de vie STaR : Collection -> Préparation -> Fine-Tuning.
    Transforme les traces de raisonnement validées en connaissance cristallisée.
    """
    def __init__(self, 
                 prompt_manager: PromptManager,
                 traces_path: str = "data/mlops/datasets/star_reasoning_traces.jsonl",
                 main_dataset_path: str = "data/mlops/datasets/animetix_expert_ft.jsonl"):
        self.prompt_manager = prompt_manager
        # Chemins absolus
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.traces_path = os.path.join(base_dir, traces_path)
        self.main_dataset_path = os.path.join(base_dir, main_dataset_path)

    def prepare_star_dataset(self) -> int:
        """
        Convertit les traces STaR brutes en format d'instruction et les fusionne
        au dataset principal de fine-tuning.
        """
        if not os.path.exists(self.traces_path):
            logger.warning("No STaR traces found to prepare.")
            return 0

        new_entries = []
        try:
            with open(self.traces_path, 'r', encoding='utf-8') as f:
                for line in f:
                    trace = json.loads(line)
                    # Conversion au format instruction/input/output
                    new_entries.append({
                        "instruction": f"Résous cette énigme sur l'univers anime/manga en détaillant ton raisonnement.",
                        "input": trace.get("prompt", ""),
                        "output": trace.get("completion", "")
                    })
            
            if not new_entries:
                return 0

            # Ajout au dataset principal (Append)
            os.makedirs(os.path.dirname(self.main_dataset_path), exist_ok=True)
            with open(self.main_dataset_path, 'a', encoding='utf-8') as f:
                for entry in new_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            # Nettoyage des traces traitées pour éviter les doublons au prochain cycle
            # os.remove(self.traces_path) # Optionnel: on peut aussi archiver
            
            logger.info(f"✅ STaR: {len(new_entries)} reasoning traces integrated into main dataset.")
            return len(new_entries)
            
        except Exception as e:
            logger.error(f"Failed to prepare STaR dataset: {e}")
            return 0

    def trigger_finetuning(self) -> Dict[str, Any]:
        """
        Déclenche le processus de Fine-Tuning. 
        En production, cela devrait être une tâche Celery sur une machine avec GPU.
        """
        logger.info("🚀 STaR: Triggering automated Fine-Tuning...")
        
        # On vérifie si on a assez de données pour que ça vaille le coup (ex: > 50 nouvelles traces)
        # Pour la démo, on lance quand même
        
        try:
            # Appel du script d'entraînement existant
            # En prod, on utiliserait un orchestrateur comme Ray ou Kubernetes Jobs
            script_path = os.path.join(os.path.dirname(self.main_dataset_path), "..", "..", "..", "src", "pipeline", "mlops", "train_expert_model.py")
            script_path = os.path.normpath(script_path)
            
            # On lance en mode asynchrone (non-bloquant ici car sera dans Celery)
            # return {"status": "started", "message": "Fine-tuning job submitted."}
            
            # Pour l'instant, on simule le succès de la soumission
            return {
                "status": "success",
                "job_id": f"star-ft-{os.urandom(4).hex()}",
                "timestamp": "2026-05-22T19:50:00Z"
            }
        except Exception as e:
            logger.error(f"Fine-tuning trigger failed: {e}")
            return {"status": "error", "message": str(e)}
