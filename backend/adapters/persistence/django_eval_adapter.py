from typing import Dict, Any
from core.ports.eval_port import EvalResultPort

class DjangoEvalAdapter(EvalResultPort):
    def save_result(self, query: str, context: str, answer: str, metrics: Dict[str, Any]) -> None:
        from animetix.models import AIREvalResult
        AIREvalResult.objects.create(
            game_mode='classic',
            input_context=f"Query: {query}\nContext: {context}",
            output_text=answer,
            faithfulness=metrics.get('faithfulness', 0.0),
            relevancy=metrics.get('answer_relevance', 0.0),
            precision=metrics.get('context_precision', 0.0),
            hallucination_detected=metrics.get('hallucination', False)
        )

    def get_evaluation_stats(self) -> Dict[str, Any]:
        from animetix.models import AIREvalResult
        from django.db.models import Avg, Count
        
        stats = AIREvalResult.objects.aggregate(
            avg_faith=Avg('faithfulness'), 
            avg_rel=Avg('relevancy'), 
            avg_prec=Avg('precision'), 
            total=Count('id')
        )
        hallucinations = AIREvalResult.objects.filter(hallucination_detected=True).count()
        
        return {
            'stats': stats,
            'hallucination_count': hallucinations
        }
