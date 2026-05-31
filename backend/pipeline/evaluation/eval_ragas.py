import os
import asyncio
import logging
from typing import List, Dict
from pipeline.chroma_client import chroma_manager
from pipeline.neo4j_client import neo4j_manager
import httpx
# --- DJANGO SETUP FOR MLOPS CONTAINERS ---
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')
django.setup()

from animetix.containers import get_container
from core.domain.services.ragas_eval_service import RagasEvalService, EvaluationResult
from sentence_transformers import SentenceTransformer
from core.utils.security import safe_http_request
logger = logging.getLogger("animetix." + __name__)

class RAGEvaluator:
    def __init__(self, brain_url: str = "http://127.0.0.1:7860"):
        self.brain_url = f"{brain_url}/generate"
        self.embed_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    def get_contexts(self, query: str, mode: str = "vector") -> List[str]:
        """Récupère le contexte. Mode: 'vector' ou 'hybrid'."""
        # 1. Retrieval Vectoriel (Chroma)
        query_embedding = self.embed_model.encode([query]).tolist()
        try:
            # On cherche dans anime_thematic car c'est la collection principale utilisée dans evaluation_metrics.py
            results = chroma_manager.query_collection("anime_thematic", query_embedding, n_results=3)
            vector_contexts = [doc for doc in results['documents'][0]]
            media_ids = [res for res in results['ids'][0]]
        except Exception as e:
            logger.error(f"Failed to query contexts for '{query}': {e}")
            vector_contexts = ["Pas de contexte trouvé."]
            media_ids = []

        if mode == "vector":
            return vector_contexts

        # 2. Retrieval Graph (Neo4j) - Enrichissement
        graph_context = neo4j_manager.get_enriched_context(media_ids)
        if graph_context:
            return vector_contexts + [f"Informations Graph complémentaires:\n{graph_context}"]
        
        return vector_contexts

    def generate_answer(self, query: str, contexts: List[str]) -> str:
        """Appelle l'API brain pour générer une réponse avec le contexte."""
        context_str = "\n".join(contexts)
        prompt = f"Contexte:\n{context_str}\n\nQuestion: {query}"
        
        try:
            response = safe_http_request("POST", self.brain_url, json={
                "prompt": prompt,
                "system_prompt": "Tu es un expert en Anime/Manga. Utilise le contexte fourni pour répondre de manière précise."
            }, timeout=60, allow_internal=True)
            if response.status_code == 200:

                return response.json().get("text", "")
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
        return "Erreur de génération."

    async def run_evaluation(self, test_questions: List[Dict[str, str]], mode: str = "vector"):
        """Lance l'évaluation RAGAS sur un set de questions."""
        logger.info(f"🚀 Starting evaluation in mode: {mode.upper()}")
        data = {
            "question": [],
            "answer": [],
            "contexts": [],
            "ground_truth": []
        }

        for item in test_questions:
            q = item["question"]
            gt = item["ground_truth"]
            
            logger.info(f"🧐 Evaluating: {q}")
            contexts = self.get_contexts(q, mode=mode)
            answer = self.generate_answer(q, contexts)
            
            data["question"].append(q)
            data["answer"].append(answer)
            data["contexts"].append(contexts)
            data["ground_truth"].append(gt)

        eval_service = RagasEvalService(judge_engine=get_container().inference_engine())
        
        faith_scores = []
        relevance_scores = []
        precision_scores = []
        recall_scores = []

        for i in range(len(data["question"])):
            q = data["question"][i]
            a = data["answer"][i]
            c_str = "\n".join(data["contexts"][i])
            gt = data["ground_truth"][i]
            
            prompt = f"""
            Évalue l'interaction RAG ci-dessous en la comparant à la Vérité Terrain (Ground Truth) attendue :
            
            Question de l'utilisateur :
            {q}
            
            Contexte de connaissances fourni :
            {c_str}
            
            Réponse générée par le système :
            {a}
            
            Vérité Terrain attendue (Ground Truth) :
            {gt}
            """
            
            try:
                res_obj = eval_service.judge_engine.generate_structured(
                    prompt=prompt,
                    response_model=EvaluationResult,
                    system_prompt="Tu es un juge sémantique d'IA impartial chargé de mesurer la qualité d'une interaction RAG."
                )
                faith_scores.append(res_obj.faithfulness)
                relevance_scores.append(res_obj.answer_relevancy)
                precision_scores.append(res_obj.context_precision)
                recall_scores.append(res_obj.context_recall if res_obj.context_recall is not None else 0.0)
            except Exception as e:
                logger.error(f"Error judging row in eval_ragas: {e}")
                faith_scores.append(0.0)
                relevance_scores.append(0.0)
                precision_scores.append(0.0)
                recall_scores.append(0.0)

        result = {
            "faithfulness": sum(faith_scores) / len(faith_scores) if faith_scores else 0.0,
            "answer_relevancy": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0,
            "context_precision": sum(precision_scores) / len(precision_scores) if precision_scores else 0.0,
            "context_recall": sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
        }
        
        logger.info(f"📊 Results ({mode}):")
        logger.info(result)
        return result

if __name__ == "__main__":
    test_set = [
        {
            "question": "Qui a écrit le manga One Piece ?",
            "ground_truth": "Eiichiro Oda"
        },
        {
            "question": "Quels sont les thèmes principaux de Naruto ?",
            "ground_truth": "Ninja, Action, Aventure, Shonen"
        }
    ]
    
    evaluator = RAGEvaluator()
    
    async def compare():
        # Évaluation Vector-only
        await evaluator.run_evaluation(test_set, mode="vector")
        # Évaluation Hybrid
        await evaluator.run_evaluation(test_set, mode="hybrid")

    asyncio.run(compare())
