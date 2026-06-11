import os
import json
import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger("animetix.mlops")

class DPOFeedbackLoop:
    """
    Automates the collection and validation of user feedback for DPO fine-tuning.
    Ensures high-quality chosen/rejected pairs.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Charger les variables d'environnement
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        load_dotenv(os.path.join(base_dir, '.env'))
        
        # Initialiser le client Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and genai is not None:
            logger.info("Initializing Gemini API client for DPO Oracle responses...")
            self.client = genai.Client(api_key=api_key)
        else:
            logger.warning("Gemini client not initialized (missing API key or google-genai dependency).")
            self.client = None

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
            
        # Quality check: avoid generic error responses
        generic_errors = ["je ne sais pas", "désolé", "erreur", "temporairement indisponible", "i am sorry"]
        if any(err in entry['output'].lower() for err in generic_errors):
            return False
            
        return True

    def generate_oracle_response(self, context_prompt: str) -> str:
        """
        Génère une réponse expert corrigée (chosen) via le modèle Oracle (Gemini).
        """
        if not self.client:
            return "Désolé, je ne dispose pas d'informations supplémentaires sur ce sujet."
            
        prompt = (
            f"Tu es un expert absolu de la japanimation, des mangas, des seiyuu et du marché français. "
            f"Génère une réponse parfaite, claire et 100% en français pour la question suivante :\n\n"
            f"{context_prompt}\n\n"
            f"Renvoie uniquement la réponse rédigée de manière fluide et naturelle, sans aucune salutation ou métadonnée."
        )
        
        model_name = os.getenv("ANIMETIX_GEMINI_MODEL", "gemini-2.5-flash")
        
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response.text:
                    time.sleep(0.5)  # Respecter le rate-limiting
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/3 failed to generate chosen response via Gemini: {e}")
                err_msg = str(e).upper()
                if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg or "UNAVAILABLE" in err_msg or "503" in err_msg:
                    sleep_time = (attempt + 1) * 15.0
                    logger.info(f"Rate limit or service unavailable detected in DPO loop. Sleeping for {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    time.sleep(1.0)
                    
        return "Désolé, je ne dispose pas d'informations supplémentaires sur ce sujet."

    def create_dpo_pair(self, entry: Dict) -> Dict:
        """
        Creates a DPO pair (Chosen/Rejected) based on user satisfaction.
        """
        prompt = f"Génère une réponse expert pour : {entry['context']}"
        
        if entry.get('is_positive'):
            return {
                "prompt": prompt,
                "chosen": entry['output'],
                "rejected": "Désolé, je ne peux pas traiter cette demande pour le moment." # Generic baseline
            }
        else:
            # For negative feedback, the output IS the rejected sample
            # We generate the chosen sample via Gemini
            chosen_response = self.generate_oracle_response(entry['context'])
            return {
                "prompt": prompt,
                "chosen": chosen_response,
                "rejected": entry['output']
            }

    def process_and_export(self, raw_data_path: str, output_path: str) -> int:
        """
        Processes raw feedback and exports a validated DPO dataset.
        """
        if not os.path.exists(raw_data_path):
            logger.warning(f"Raw data path {raw_data_path} does not exist.")
            return 0
            
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

if __name__ == "__main__":
    # Example standalone usage
    loop = DPOFeedbackLoop(data_dir="data/mlops/datasets")
    loop.process_and_export(
        raw_data_path="data/mlops/datasets/ai_feedback.jsonl",
        output_path="data/mlops/datasets/dpo_train_v2.jsonl"
    )
