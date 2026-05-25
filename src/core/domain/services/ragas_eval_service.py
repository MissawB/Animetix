import logging
import asyncio
from typing import List, Dict, Any, Optional

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

from core.ports.inference_port import InferencePort
from core.ports.eval_port import EvalResultPort
from core.ports.gold_dataset_port import GoldDatasetPort
from adapters.inference.langchain_adapter import LangChainInferenceAdapter

logger = logging.getLogger("animetix.ragas")

class RagasEvalService:
    """
    Service d'évaluation RAG utilisant le framework RAGAS.
    Mesure mathématiquement la qualité du RAG (Faithfulness, Relevancy, Precision).
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
        
        # Wrap our inference engine into a LangChain compatible object for Ragas
        self.langchain_llm = LangChainInferenceAdapter(inference_engine=judge_engine)

    def evaluate_response(self, query: str, context: str, response: str) -> Dict[str, float]:
        """
        Calcule les scores de qualité pour une interaction RAG donnée via RAGAS.
        """
        # Prepare data for RAGAS
        data = {
            "question": [query],
            "contexts": [[context]],
            "answer": [response]
        }
        dataset = Dataset.from_dict(data)
        
        try:
            # Run evaluation
            # Note: Ragas metrics might require an embedding model. 
            # If not provided, it might try to use default OpenAI embeddings.
            # For now we use the LLM-based metrics.
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision],
                llm=self.langchain_llm
            )
            
            scores = {
                "faithfulness": float(result["faithfulness"]),
                "answer_relevancy": float(result["answer_relevancy"]),
                "context_precision": float(result["context_precision"])
            }
            
            # Hallucination detection
            hallucination = scores['faithfulness'] < 0.5
            
            # Persistence via Port
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
            logger.error(f"RAGAS evaluation failed: {e}")
            # Fallback to neutral scores if evaluation fails
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0
            }

    def run_batch_evaluation(self) -> Dict[str, Any]:
        """
        Charge les entrées du Gold Dataset et lance une suite complète d'évaluation RAGAS.
        Compare les réponses générées par le système contre la vérité terrain (ground truth).
        """
        if not self.gold_port:
            logger.error("GoldDatasetPort is required for batch evaluation")
            return {}
            
        entries = self.gold_port.get_all_entries()
        if not entries:
            logger.warning("No entries found in Gold Dataset")
            return {}
            
        logger.info(f"Running batch evaluation on {len(entries)} entries")
        
        questions = []
        contexts = []
        answers = []
        ground_truths = []
        
        for entry in entries:
            # We assume the Gold Dataset entry has these fields or similar
            questions.append(entry.get('question', ''))
            contexts.append([entry.get('context', '')])
            answers.append(entry.get('answer', '')) # This should be the system generated answer
            ground_truths.append(entry.get('ground_truth', ''))
            
        data = {
            "question": questions,
            "contexts": contexts,
            "answer": answers,
            "ground_truth": ground_truths
        }
        dataset = Dataset.from_dict(data)
        
        try:
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision],
                llm=self.langchain_llm
            )
            
            logger.info(f"Batch evaluation complete: {result}")
            
            # We can also save individual results if needed, 
            # but Ragas result already contains the aggregated scores.
            return dict(result)
            
        except Exception as e:
            logger.error(f"RAGAS batch evaluation failed: {e}")
            return {}
