import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from .prompt_manager import PromptManager

logger = logging.getLogger("animetix.mlops")

class DPOFeedbackLoop:
    """
    Automates the collection and validation of user feedback for DPO fine-tuning.
    Ensures high-quality chosen/rejected pairs.
    """
    DEFAULT_REJECTED_RESPONSE = "Désolé, je ne peux pas traiter cette demande pour le moment."

    def __init__(self, data_dir: str = "data/mlops/datasets", prompt_manager: PromptManager = None):
        self.data_dir = data_dir
        self.prompt_manager = prompt_manager
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create DPO data directory {data_dir}: {e}")

    def validate_feedback(self, entry: Dict) -> bool:
        """
        Rigorous validation of a feedback entry.
        Filters out low-signal data.
        """
        if not entry.get('context') or not entry.get('output'):
            return False
        
        # Length check
        if len(entry['output']) < 15:
            return False
        
        if len(entry.get('context', '')) < 5: # Added: check for non-trivial context
            return False
            
        # Quality check: avoid generic error responses
        generic_errors = ["je ne sais pas", "désolé", "erreur", "temporairement indisponible", "i am sorry"]
        if any(err in entry['output'].lower() for err in generic_errors):
            return False
            
        return True

    def create_dpo_pair(self, entry: Dict, chosen_override: str = None) -> Dict:
        """
        Creates a DPO pair (Chosen/Rejected) based on user satisfaction.
        """
        # Robust prompt generation
        if self.prompt_manager:
            prompt, _ = self.prompt_manager.get_prompt("dpo_expert_response", context=entry['context'])
        else:
            prompt = f"Context: {entry['context']}\nResponse:"
        
        if entry.get('is_positive'):
            return {
                "prompt": prompt,
                "chosen": entry['output'],
                "rejected": self.DEFAULT_REJECTED_RESPONSE
            }
        else:
            chosen = chosen_override or "RÉPONSE_À_GÉNÉRER_PAR_MODÈLE_ORACLE"
            return {
                "prompt": prompt,
                "chosen": chosen,
                "rejected": entry['output']
            }

    def process_and_export(self, raw_data_path: str, output_path: str) -> int:
        """
        Processes raw feedback and exports a validated DPO dataset.
        """
        if not os.path.exists(raw_data_path):
            logger.warning(f"Raw data path {raw_data_path} does not exist.")
            return 0
            
        logger.info("📥 Exporting User Feedback for DPO...")
        processed_count = 0
        with open(output_path, 'w', encoding='utf-8') as out_f:
            with open(raw_data_path, 'r', encoding='utf-8') as in_f:
                for line in in_f:
                    try:
                        fb = json.loads(line)
                        if self.validate_feedback(fb):
                            pair = self.create_dpo_pair(fb)
                            out_f.write(json.dumps(pair, ensure_ascii=False) + '\n')
                            processed_count += 1
                    except json.JSONDecodeError:
                        continue
                        
        logger.info(f"✨ DPO Export complete: {processed_count} pairs validated and saved to {output_path}")
        return processed_count

    def export_preference_dataset(self):
        """Export from Django models (used by tests)."""
        from animetix.models import AIFeedback
        feedbacks = AIFeedback.objects.all()
        output_path = os.path.join(self.data_dir, "dpo_export.jsonl")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for fb in feedbacks:
                entry = {
                    'context': fb.input_context,
                    'output': fb.output_text,
                    'is_positive': fb.is_positive
                }
                if self.validate_feedback(entry):
                    f.write(json.dumps(self.create_dpo_pair(entry), ensure_ascii=False) + '\n')

    def get_rejected_for_curation(self, limit: int = 100) -> List[Dict]:
        """
        Retrieves negative feedback entries for Swarm curation.
        """
        from animetix.models import AIFeedback
        feedbacks = AIFeedback.objects.filter(is_positive=False)[:limit]
        
        results = []
        for fb in feedbacks:
            entry = {
                'id': fb.id,
                'context': fb.input_context,
                'output': fb.output_text,
                'is_positive': fb.is_positive
            }
            if self.validate_feedback(entry):
                results.append(entry)
        
        return results

    def analyze_feedback_trends(self) -> Dict:
        """Analyzes recent feedback to detect performance drops."""
        from animetix.models import AIFeedback
        from django.db.models import Count, Avg
        
        total = AIFeedback.objects.count()
        if total == 0: return {"satisfaction_rate": 0, "top_failures": []}
        
        pos = AIFeedback.objects.filter(is_positive=True).count()
        neg_entries = AIFeedback.objects.filter(is_positive=False)[:10]
        
        return {
            "satisfaction_rate": (pos / total) * 100,
            "top_failures": [{"input_context": fb.input_context} for fb in neg_entries]
        }

if __name__ == "__main__":
    loop = DPOFeedbackLoop()
    loop.process_and_export(
        raw_data_path="data/mlops/datasets/ai_feedback.jsonl",
        output_path="data/mlops/datasets/dpo_train_v2.jsonl"
    )
