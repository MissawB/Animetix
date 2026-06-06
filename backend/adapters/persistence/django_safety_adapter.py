from typing import List, Dict, Any, Optional
from core.ports.safety_port import SafetyPort
from animetix.models import AISafetyEvent
from django.db.models import Count
from django.contrib.auth.models import User

class DjangoSafetyAdapter(SafetyPort):
    def log_safety_event(self,
                        event_type: str,
                        action_taken: str,
                        detected_categories: List[str] = None,
                        input_text: str = "",
                        output_text: str = "",
                        reasoning: str = "",
                        user_id: Optional[int] = None) -> Any:

        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        return AISafetyEvent.objects.create(
            user=user,
            event_type=event_type,
            action_taken=action_taken,
            detected_categories=detected_categories or [],
            input_text=input_text,
            output_text=output_text,
            reasoning=reasoning
        )

    def get_safety_stats(self) -> Dict[str, Any]:
        total_blocked = AISafetyEvent.objects.filter(action_taken__in=['block', 'rewrite']).count()
        total_events = AISafetyEvent.objects.count()

        # Categories distribution
        categories = {}
        events = AISafetyEvent.objects.all()
        for event in events:
            for cat in event.detected_categories:
                categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_violations": total_events,
            "blocked_count": total_blocked,
            "safety_health_score": round((1 - (total_blocked / max(1, total_events / 100))) * 100, 1), # Simulated formula
            "category_distribution": categories
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        events = AISafetyEvent.objects.all().order_by('-created_at')[:limit]
        return [
            {
                "id": e.id,
                "timestamp": e.created_at.isoformat(),
                "event_type": e.event_type,
                "action": e.action_taken,
                "categories": e.detected_categories,
                "input_snippet": e.input_text[:100] + "..." if len(e.input_text) > 100 else e.input_text,
                "reasoning": e.reasoning
            }
            for e in events
        ]
