import pytest
import os
import json
from django.core.management import call_command
from animetix.models import AIFeedback, GameplaySession
from django.conf import settings

@pytest.mark.django_db
def test_export_rlhf_data_command(tmp_path):
    """Vérifie que la commande d'export génère correctement les fichiers JSONL."""
    
    # 1. Créer des données de test
    AIFeedback.objects.create(
        feedback_type="similarity",
        input_context="Test context",
        output_text="Test output long enough for filter",
        is_positive=True
    )
    
    GameplaySession.objects.create(
        game_mode="classic",
        media_type="anime",
        target_item="Naruto",
        history=[{"q": "Ninja?", "a": "Yes"}],
        was_won=True
    )
    
    # 2. Mock du settings pour rediriger l'export vers un dossier temporaire
    # Note: On doit s'assurer que la commande utilise le bon dossier de sortie
    # Pour ce test, on va vérifier la création dans le dossier configuré
    
    output_dir = os.path.join(os.path.dirname(settings.BASE_DIR), 'data', 'mlops', 'datasets')
    os.makedirs(output_dir, exist_ok=True)
    
    # 3. Exécuter la commande
    call_command('export_rlhf_data')
    
    # 4. Vérifications
    feedback_file = os.path.join(output_dir, 'ai_feedback.jsonl')
    session_file = os.path.join(output_dir, 'gameplay_sessions.jsonl')
    
    assert os.path.exists(feedback_file)
    assert os.path.exists(session_file)
    
    with open(feedback_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) >= 1
        data = json.loads(lines[0])
        assert data['context'] == "Test context"
        assert data['is_positive'] is True

    with open(session_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) >= 1
        data = json.loads(lines[0])
        assert data['target'] == "Naruto"
        assert data['was_won'] is True
