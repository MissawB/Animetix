import os
import asyncio
import logging
from typing import List, Dict
from pipeline.chroma_client import chroma_manager
from pipeline.neo4j_client import neo4j_manager
import httpx
from ragas import evaluate
from datasets import Dataset
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("animetix." + __name__)

# Configuration de l'LLM de jugement (Gemini)
eval_llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Configuration des embeddings pour RAGAS
eval_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)
ragas_embeddings = LangchainEmbeddingsWrapper(eval_embeddings)

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
            response = httpx.post(self.brain_url, json={
                "prompt": prompt,
                "system_prompt": "Tu es un expert en Anime/Manga. Utilise le contexte fourni pour répondre de manière précise."
            }, timeout=60, follow_redirects=True)
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

        dataset = Dataset.from_dict(data)
        
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall
            ],
            llm=eval_llm,
            embeddings=ragas_embeddings
        )
        
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
