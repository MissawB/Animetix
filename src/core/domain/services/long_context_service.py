import random
import time
import logging
from typing import List, Dict, Optional
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.benchmark")

class LongContextDiscoveryService:
    """
    Service de test et de gestion des contextes longs.
    Implémente la logique 'Needle In A Haystack' pour évaluer la mémoire du LLM.
    """
    def __init__(self, inference_engine: InferencePort):
        self.inference_engine = inference_engine

    def create_haystack(self, filler_text: str, needle: str, target_token_count: int, needle_position: float = 0.5) -> str:
        """
        Génère une 'botte de foin' de texte avec une 'aiguille' (information) cachée à une position précise.
        needle_position: entre 0.0 (début) et 1.0 (fin).
        """
        # Simulation simplifiée : on répète le texte de remplissage jusqu'à atteindre la taille
        # (Dans un vrai test, on utiliserait un tokenizer pour compter précisément)
        words = filler_text.split()
        current_text = words * (target_token_count // max(1, len(words)))
        
        insert_idx = int(len(current_text) * needle_position)
        current_text.insert(insert_idx, f"\n--- INFORMATION SECRÈTE : {needle} ---\n")
        
        return " ".join(current_text)

    def run_needle_test(self, needle: str, question: str, context_size: int, position: float) -> Dict:
        """
        Exécute un test de rappel sur un contexte long.
        """
        filler = "L'anime est un média japonais fascinant avec de nombreux genres comme le Shounen, le Seinen et le Shojo."
        haystack = self.create_haystack(filler, needle, context_size, position)
        
        start_time = time.time()
        response = self.inference_engine.generate(
            prompt=f"Lis attentivement ce texte et réponds à la question.\n\nTEXTE :\n{haystack}\n\nQUESTION : {question}",
            system_prompt="Tu es un testeur de mémoire haute précision. Réponds de manière concise."
        )
        duration = time.time() - start_time
        
        # Vérification si l'aiguille est présente dans la réponse
        success = needle.lower() in response.lower()
        
        return {
            "context_size": context_size,
            "needle_position": position,
            "success": success,
            "response": response,
            "latency_sec": duration
        }

    def benchmark_model_limits(self, sizes=[2000, 8000, 16000, 32000]):
        """
        Lance une série de tests pour cartographier les limites de rappel du modèle.
        """
        results = []
        needle = "Le code secret du coffre de Spike Spiegel est 1234."
        question = "Quel est le code secret du coffre de Spike Spiegel ?"
        
        for size in sizes:
            for pos in [0.1, 0.5, 0.9]: # Début, Milieu, Fin
                logger.info(f"📊 Testing Size: {size}, Position: {pos}...")
                res = self.run_needle_test(needle, question, size, pos)
                results.append(res)
                
        return results
