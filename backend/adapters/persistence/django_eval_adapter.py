from typing import Dict, Any
from core.ports.eval_port import EvalResultPort

class DjangoEvalAdapter(EvalResultPort):
    def save_result(self, query: str, context: str, answer: str, metrics: Dict[str, float]) -> None:
        from animetix.models import AIREvalResult
        AIREvalResult.objects.create(
            query=query,
            context=context,
            answer=answer,
            faithfulness=metrics.get('faithfulness', 0.0),
            answer_relevance=metrics.get('answer_relevance', 0.0),
            context_precision=metrics.get('context_precision', 0.0),
            context_recall=metrics.get('context_recall', 0.0)
        )

    def get_evaluation_stats(self) -> Dict[str, Any]:
        from animetix.models import AIREvalResult
        from django.db.models import Avg, Count
        
        stats = AIREvalResult.objects.aggregate(
            avg_faith=Avg('faithfulness'), 
            avg_rel=Avg('answer_relevance'), 
            avg_prec=Avg('context_precision'), 
            total=Count('id')
        )
        hallucinations = AIREvalResult.objects.filter(hallucination_detected=True).count()
        
        return {
            'stats': stats,
            'hallucination_count': hallucinations
        }
