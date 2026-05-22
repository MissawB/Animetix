import os
import json
import logging
from typing import List, Dict, Optional
from core.ports.inference_port import InferencePort
from core.domain.services.prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")

class StarReasonerService:
    """
    Implémentation de STaR (Self-Taught Reasoner).
    """
    def __init__(self, inference_engine: InferencePort, prompt_manager: PromptManager, training_data_path: str = "data/mlops/datasets/star_reasoning_traces.jsonl"):
        self.inference_engine = inference_engine
        self.prompt_manager = prompt_manager
        self.training_data_path = training_data_path

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
                
        # Sauvegarde des traces correctes pour l'auto-amélioration
        if successful_paths:
            self._save_traces(successful_paths)
            logger.info(f"✅ STaR: Found {len(successful_paths)} correct reasoning paths. Traces saved for Fine-Tuning.")
            
            # Déclenchement automatique de la boucle MLOps (via Celery)
            try:
                from backend.animetix.tasks import run_star_training_cycle_task
                # On déclenche la tâche si on vient d'ajouter des traces
                run_star_training_cycle_task.delay()
            except ImportError:
                logger.warning("Celery task run_star_training_cycle_task not available.")
        else:
            logger.info("❌ STaR: Failed to find the correct answer in all attempts.")
            
        return {
            "success": len(successful_paths) > 0,
            "best_response": best_answer,
            "traces_saved": len(successful_paths)
        }

    def _save_traces(self, paths: List[Dict]):
        """Sauvegarde les traces de raisonnement correctes pour un futur fine-tuning."""
        os.makedirs(os.path.dirname(self.training_data_path), exist_ok=True)
        with open(self.training_data_path, 'a', encoding='utf-8') as f:
            for path in paths:
                # Format compatible avec TRL SFTTrainer
                training_example = {
                    "prompt": path["riddle"],
                    "completion": path["reasoning_trace"]
                }
                f.write(json.dumps(training_example) + "\n")
