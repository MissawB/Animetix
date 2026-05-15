import json
import os
from django.core.management.base import BaseCommand
from animetix.models import AIFeedback, GameplaySession
from django.conf import settings

class Command(BaseCommand):
    help = 'Export RLHF and game session data for LLM fine-tuning'

    def handle(self, *args, **options):
        # Chemins de sortie
        base_dir = settings.BASE_DIR
        output_dir = os.path.join(os.path.dirname(base_dir), 'data', 'mlops', 'datasets')
        os.makedirs(output_dir, exist_ok=True)

        # 1. Export AIFeedback (Direct Preference / Pairwise)
        feedback_path = os.path.join(output_dir, 'ai_feedback.jsonl')
        with open(feedback_path, 'w', encoding='utf-8') as f:
            for fb in AIFeedback.objects.all().iterator():
                entry = {
                    'type': fb.feedback_type,
                    'context': fb.input_context,
                    'output': fb.output_text,
                    'is_positive': fb.is_positive,
                    'timestamp': fb.created_at.isoformat()
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        self.stdout.write(self.style.SUCCESS(f'Exported feedback entries to {feedback_path}.'))

        # 2. Export GameplaySession (Logic and Fact validation)
        session_path = os.path.join(output_dir, 'gameplay_sessions.jsonl')
        with open(session_path, 'w', encoding='utf-8') as f:
            for session in GameplaySession.objects.all().iterator():
                entry = {
                    'game_mode': session.game_mode,
                    'media_type': session.media_type,
                    'target': session.target_item,
                    'history': session.history,
                    'was_won': session.was_won,
                    'timestamp': session.created_at.isoformat()
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
        self.stdout.write(self.style.SUCCESS(f'Exported gameplay sessions to {session_path}.'))
