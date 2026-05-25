from typing import List, Dict, Any, Optional
from core.ports.gold_dataset_port import GoldDatasetPort

class DjangoGoldDatasetAdapter(GoldDatasetPort):
    def get_all_entries(self) -> List[Dict[str, Any]]:
        from animetix.models import GoldDatasetEntry
        entries = GoldDatasetEntry.objects.all().order_by('-created_at')
        return [self._to_dict(e) for e in entries]

    def sync_positive_feedback(self) -> int:
        from animetix.models import AIFeedback, GoldDatasetEntry
        positive_feedbacks = AIFeedback.objects.filter(is_positive=True).exclude(golddatasetentry__isnull=False)
        count = 0
        for fb in positive_feedbacks:
            GoldDatasetEntry.objects.create(
                context=fb.input_context, 
                instruction="Réponds à la question de l'utilisateur sur l'anime/manga.", 
                response=fb.output_text, 
                source_feedback=fb
            )
            count += 1
        return count

    def validate_entry(self, entry_id: int) -> bool:
        from animetix.models import GoldDatasetEntry
        try:
            entry = GoldDatasetEntry.objects.get(id=entry_id)
            entry.is_validated = True
            entry.save()
            return True
        except GoldDatasetEntry.DoesNotExist:
            return False

    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        from animetix.models import GoldDatasetEntry
        try:
            entry = GoldDatasetEntry.objects.get(id=entry_id)
            return self._to_dict(entry)
        except GoldDatasetEntry.DoesNotExist:
            return None

    def _to_dict(self, entry) -> Dict[str, Any]:
        return {
            'id': entry.id,
            'context': entry.context,
            'instruction': entry.instruction,
            'response': entry.response,
            'is_validated': entry.is_validated,
            'created_at': entry.created_at
        }
