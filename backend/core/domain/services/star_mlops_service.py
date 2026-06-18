import json
import logging
import os
from typing import Any, Dict

from core.domain.services.prompt_manager import PromptManager
from core.ports.gold_dataset_port import GoldDatasetPort

logger = logging.getLogger("animetix.mlops.star")


class StarMLOpsDomainService:
    """
    Orchestre le cycle de vie STaR : Collection -> Préparation -> Fine-Tuning.
    Transforme les traces de raisonnement validées en connaissance cristallisée.
    """

    def __init__(
        self,
        prompt_manager: PromptManager,
        gold_dataset_port: GoldDatasetPort,
        eval_service=None,
        main_dataset_path: str = "data/mlops/datasets/animetix_expert_ft.jsonl",
    ):
        self.prompt_manager = prompt_manager
        self.gold_dataset_port = gold_dataset_port
        self.eval_service = eval_service
        # Chemins absolus
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        self.main_dataset_path = os.path.join(base_dir, main_dataset_path)

    def prepare_star_dataset(self) -> int:
        """
        Récupère les traces STaR validées par un humain depuis la DB
        et les exporte vers le dataset principal de fine-tuning.
        """
        entries = self.gold_dataset_port.get_unprocessed_validated_entries()

        if not entries:
            logger.info("No new validated STaR traces found for export.")
            return 0

        new_entries_formatted = []
        entry_ids = []

        try:
            for entry in entries:
                # Conversion au format instruction/input/output
                new_entries_formatted.append(
                    {
                        "instruction": entry.get("instruction", "Résous cette énigme."),
                        "input": entry.get(
                            "context", ""
                        ),  # Le context contient le riddle
                        "output": entry.get(
                            "response", ""
                        ),  # La response contient le raisonnement complet
                    }
                )
                entry_ids.append(entry["id"])

            # Ajout au dataset principal (Append)
            os.makedirs(os.path.dirname(self.main_dataset_path), exist_ok=True)
            with open(self.main_dataset_path, "a", encoding="utf-8") as f:
                for entry_data in new_entries_formatted:
                    f.write(json.dumps(entry_data, ensure_ascii=False) + "\n")

            # Nettoyage des entrées traitées (retrait de la DB)
            self.gold_dataset_port.mark_entries_as_processed(entry_ids)

            logger.info(
                f"✅ STaR: {len(new_entries_formatted)} human-validated reasoning traces exported to FT dataset."
            )
            return len(new_entries_formatted)

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
            script_path = os.path.join(
                os.path.dirname(self.main_dataset_path),
                "..",
                "..",
                "..",
                "src",
                "pipeline",
                "mlops",
                "train_expert_model.py",
            )
            script_path = os.path.normpath(script_path)

            # On lance en mode asynchrone (non-bloquant ici car sera dans Celery)
            # return {"status": "started", "message": "Fine-tuning job submitted."}

            # Pour l'instant, on simule le succès de la soumission
            return {
                "status": "success",
                "job_id": f"star-ft-{os.urandom(4).hex()}",
                "timestamp": "2026-05-22T19:50:00Z",
            }
        except Exception as e:
            logger.error(f"Fine-tuning trigger failed: {e}")
            return {"status": "error", "message": str(e)}
