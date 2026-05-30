import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.ports.inference_port import InferencePort
from core.ports.eval_port import EvalResultPort
from core.ports.gold_dataset_port import GoldDatasetPort

logger = logging.getLogger("animetix.ragas")

class EvaluationResult(BaseModel):
    faithfulness: float = Field(
        ..., 
        description="Score entre 0.0 et 1.0. Fidélité de la réponse par rapport au contexte (1.0 = parfaitement fidèle, aucun fait n'est inventé ou extrapolé; 0.0 = pure invention/hallucination complète)."
    )
    answer_relevancy: float = Field(
        ..., 
        description="Score entre 0.0 et 1.0. Pertinence de la réponse par rapport à la question posée (1.0 = la réponse répond directement, complètement et précisément à la question; 0.0 = hors-sujet complet)."
    )
    context_precision: float = Field(
        ..., 
        description="Score entre 0.0 et 1.0. Utilité et pertinence du contexte récupéré pour répondre à la question (1.0 = contexte extrêmement précis et sans bruit; 0.0 = contexte totalement inutile)."
    )
    context_recall: Optional[float] = Field(
        None, 
        description="Score entre 0.0 et 1.0. Rappel du contexte par rapport à la Vérité Terrain (1.0 = le contexte contient 100% des faits attendus dans la Vérité Terrain; 0.0 = le contexte ne contient aucun des faits requis)."
    )

class RagasEvalService:
    """
    Service d'évaluation RAG autonome utilisant un juge LLM structuré.
    Mesure mathématiquement la fidélité, la pertinence, la précision et le rappel du système,
    sans aucune dépendance envers LangChain ou Ragas.
    """
    def __init__(
        self, 
        judge_engine: InferencePort, 
        eval_port: Optional[EvalResultPort] = None,
        gold_port: Optional[GoldDatasetPort] = None
    ):
        self.judge_engine = judge_engine
        self.eval_port = eval_port
        self.gold_port = gold_port

    def evaluate_response(self, query: str, context: str, response: str) -> Dict[str, float]:
        """
        Calcule les scores de qualité pour une interaction RAG donnée via notre juge LLM.
        """
        prompt = f"""
        Évalue l'interaction RAG suivante de manière objective :
        
        Question de l'utilisateur :
        {query}
        
        Contexte de connaissances fourni :
        {context}
        
        Réponse générée par le système :
        {response}
        
        Calcule les trois métriques requises :
        1. faithfulness (Fidélité de la réponse)
        2. answer_relevancy (Pertinence de la réponse)
        3. context_precision (Précision du contexte)
        """
        
        try:
            result = self.judge_engine.generate_structured(
                prompt=prompt,
                response_model=EvaluationResult,
                system_prompt="Tu es un juge IA impartial chargé de mesurer la qualité des réponses d'un système RAG."
            )
            
            scores = {
                "faithfulness": float(result.faithfulness),
                "answer_relevancy": float(result.answer_relevancy),
                "context_precision": float(result.context_precision)
            }
            
            # Détection d'hallucinations
            hallucination = scores['faithfulness'] < 0.5
            
            # Persistance via Port
            if self.eval_port:
                metrics = {
                    'faithfulness': scores['faithfulness'],
                    'answer_relevance': scores['answer_relevancy'],
                    'context_precision': scores['context_precision'],
                    'hallucination': hallucination
                }
                self.eval_port.save_result(query, context, response, metrics)
                
            return scores
            
        except Exception as e:
            logger.error(f"LLM-as-a-judge evaluation failed: {e}")
            # Fallback en cas d'échec
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0
            }

    def run_batch_evaluation(self) -> Dict[str, Any]:
        """
        Charge les entrées du Gold Dataset et lance une évaluation par lot complète.
        Compare les réponses générées contre la vérité terrain (ground truth) et retourne les moyennes globales.
        """
        if not self.gold_port:
            logger.error("GoldDatasetPort is required for batch evaluation")
            return {}
            
        entries = self.gold_port.get_all_entries()
        if not entries:
            logger.warning("No entries found in Gold Dataset")
            return {}
            
        logger.info(f"Running batch evaluation on {len(entries)} entries")
        
        total_faith = 0.0
        total_relevancy = 0.0
        total_precision = 0.0
        total_recall = 0.0
        valid_count = 0
        
        for entry in entries:
            q = entry.get('question', '')
            c = entry.get('context', '')
            a = entry.get('answer', '')
            gt = entry.get('ground_truth', '')
            
            if not q or not c or not a:
                continue
                
            prompt = f"""
            Évalue l'interaction RAG ci-dessous en la comparant à la Vérité Terrain (Ground Truth) attendue :
            
            Question :
            {q}
            
            Contexte de connaissances fourni :
            {c}
            
            Réponse générée :
            {a}
            
            Vérité Terrain attendue (Ground Truth) :
            {gt}
            
            Calcule les quatre métriques :
            1. faithfulness (Fidélité de la réponse par rapport au contexte)
            2. answer_relevancy (Pertinence de la réponse par rapport à la question)
            3. context_precision (Précision du contexte par rapport à la question)
            4. context_recall (Rappel du contexte : contient-il bien les informations de la Vérité Terrain ?)
            """
            
            try:
                result = self.judge_engine.generate_structured(
                    prompt=prompt,
                    response_model=EvaluationResult,
                    system_prompt="Tu es un expert en évaluation sémantique de systèmes de RAG d'intelligence artificielle."
                )
                
                total_faith += result.faithfulness
                total_relevancy += result.answer_relevancy
                total_precision += result.context_precision
                total_recall += result.context_recall if result.context_recall is not None else 0.0
                valid_count += 1
                
            except Exception as e:
                logger.error(f"Failed to evaluate batch item '{q}': {e}")
                
        if valid_count == 0:
            return {}
            
        avg_scores = {
            "faithfulness": total_faith / valid_count,
            "answer_relevancy": total_relevancy / valid_count,
            "context_precision": total_precision / valid_count,
            "context_recall": total_recall / valid_count
        }
        
        logger.info(f"Batch evaluation completed successfully for {valid_count} entries : {avg_scores}")
        return avg_scores
