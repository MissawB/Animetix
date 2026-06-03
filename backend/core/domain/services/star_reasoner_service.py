import os
import json
import logging
from typing import List, Dict, Optional
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager
from core.ports.gold_dataset_port import GoldDatasetPort

logger = logging.getLogger("animetix.mlops")

class StarReasonerService:
    """
    Implémentation de STaR (Self-Taught Reasoner).
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, gold_dataset_port: GoldDatasetPort):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.gold_dataset_port = gold_dataset_port

    def solve_riddle_with_star(self, riddle: str, expected_answer: str, num_attempts: int = 3) -> Dict:
        """
        Tente de résoudre une énigme en générant plusieurs chemins de raisonnement.
        """
        logger.info(f"🧠 STaR: Generating {num_attempts} reasoning paths for riddle...")
        successful_paths = []
        best_answer = "Désolé, je n'ai pas pu résoudre l'énigme."
        
        for i in range(num_attempts):
            prompt, system = self.prompt_manager.get_prompt(
                "star_reasoner_thought",
                riddle=riddle
            )
            response = self.inference_engine.generate(prompt, system_prompt=system)
            
            # Extraction de la réponse finale
            final_answer = ""
            if "FINAL_ANSWER:" in response:
                final_answer = response.split("FINAL_ANSWER:")[-1].strip()
            
            # Vérification de la justesse (évaluation simplifiée)
            is_correct = expected_answer.lower() in final_answer.lower()
            
            path_data = {
                "riddle": riddle,
                "reasoning_trace": response,
                "final_answer": final_answer,
                "is_correct": is_correct
            }
            
            if is_correct:
                successful_paths.append(path_data)
                best_answer = response
                
        # Sauvegarde des traces correctes pour validation humaine (et auto-amélioration future)
        if successful_paths:
            self._save_traces(successful_paths)
            logger.info(f"✅ STaR: Found {len(successful_paths)} correct reasoning paths. Traces saved for human validation.")
            
            # Déclenchement automatique de la boucle MLOps (via Cloud Tasks)
            try:
                from animetix.tasks_client import enqueue_task
                # On déclenche la tâche si on vient d'ajouter des traces
                enqueue_task("run_star_training_cycle_task")
            except Exception as e:
                logger.warning(f"Failed to enqueue run_star_training_cycle_task: {e}")
        else:
            logger.info("❌ STaR: Failed to find the correct answer in all attempts.")
            
        return {
            "success": len(successful_paths) > 0,
            "best_response": best_answer,
            "traces_saved": len(successful_paths)
        }

    def _save_traces(self, paths: List[Dict]):
        """Sauvegarde les traces de raisonnement correctes pour validation humaine via la BD."""
        for path in paths:
            self.gold_dataset_port.save_star_trace(
                instruction="Résous cette énigme sur l'univers anime/manga en détaillant ton raisonnement.",
                input_text=path["riddle"],
                output_text=path["reasoning_trace"]
            )
