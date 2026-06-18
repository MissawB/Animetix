from typing import List, Dict, Any
from core.ports.feedback_port import FeedbackRepositoryPort


class DjangoFeedbackAdapter(FeedbackRepositoryPort):
    def save_feedback(
        self,
        input_context: str,
        output_text: str,
        is_positive: bool,
        user_id: Any = None,
        feedback_type: str = "general",
    ) -> None:
        from animetix.models import AIFeedback  # noqa: E402

        AIFeedback.objects.create(
            input_context=input_context,
            output_text=output_text,
            is_positive=is_positive,
            user_id=user_id,
            feedback_type=feedback_type,
        )

    def get_recent_feedback(
        self, limit: int = 100, feedback_type: str = None
    ) -> List[Dict[str, Any]]:
        from animetix.models import AIFeedback  # noqa: E402

        query = AIFeedback.objects.all()
        if feedback_type:
            query = query.filter(feedback_type=feedback_type)
        feedbacks = query.order_by("-created_at")[:limit]
        return [
            {
                "id": fb.id,
                "input_context": fb.input_context,
                "output_text": fb.output_text,
                "is_positive": fb.is_positive,
                "created_at": fb.created_at,
                "feedback_type": fb.feedback_type,
            }
            for fb in feedbacks
        ]

    def get_feedback_stats(self) -> Dict[str, Any]:
        from animetix.models import AIFeedback  # noqa: E402

        total = AIFeedback.objects.count()
        if total == 0:
            return {"satisfaction_rate": 0, "total": 0, "top_failures": []}

        pos = AIFeedback.objects.filter(is_positive=True).count()
        negatives = AIFeedback.objects.filter(is_positive=False).order_by(
            "-created_at"
        )[:5]

        top_failures = []
        for neg in negatives:
            top_failures.append(
                {
                    "id": neg.id,
                    "input_context": neg.input_context,
                    "output_text": neg.output_text,
                }
            )

        return {
            "satisfaction_rate": (pos / total) * 100,
            "total": total,
            "top_failures": top_failures,
        }

    def get_user_feedback(self, user_id: Any, limit: int = 100) -> List[Dict[str, Any]]:
        from animetix.models import AIFeedback  # noqa: E402

        feedbacks = AIFeedback.objects.filter(user_id=user_id).order_by("-created_at")[
            :limit
        ]
        return [
            {
                "id": fb.id,
                "input_context": fb.input_context,
                "output_text": fb.output_text,
                "is_positive": fb.is_positive,
                "created_at": fb.created_at,
                "feedback_type": fb.feedback_type,
            }
            for fb in feedbacks
        ]
