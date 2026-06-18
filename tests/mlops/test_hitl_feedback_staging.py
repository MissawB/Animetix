import pytest
from animetix.models import AIFeedback, GoldDatasetEntry


@pytest.mark.django_db
def test_simple_feedback_not_staged():
    # 1. Clear existing entries
    GoldDatasetEntry.objects.all().delete()

    # 2. Create simple feedback (should NOT be staged because it's not complex)
    simple_fb = AIFeedback.objects.create(
        input_context="Qui est Luffy ?",
        output_text="Le protagoniste de One Piece.",
        is_positive=True,
        feedback_type="general",
    )

    assert not GoldDatasetEntry.objects.filter(source_feedback=simple_fb).exists()


@pytest.mark.django_db
def test_complex_feedback_automatically_staged():
    # 1. Clear existing entries
    GoldDatasetEntry.objects.all().delete()

    # 2. Create complex feedback (contains high-complexity keywords like 'paradoxe' and 'scénario')
    complex_fb = AIFeedback.objects.create(
        input_context="Explique le paradoxe temporel dans le scénario de Steins;Gate.",
        output_text="Le paradoxe de Steins;Gate implique le saut temporel via un micro-ondes connecté à un téléphone portable.",
        is_positive=True,
        feedback_type="general",
    )

    # Assert a GoldDatasetEntry was automatically created in the HITL moderation queue
    entry = GoldDatasetEntry.objects.filter(source_feedback=complex_fb).first()
    assert entry is not None
    assert entry.is_validated is False  # Awaiting human validation (HITL)
    assert entry.context == complex_fb.input_context
    assert entry.instruction == complex_fb.input_context
    assert entry.response == complex_fb.output_text
    assert entry.metadata.get("is_complex_user_query") is True
    assert entry.metadata.get("staged_from_feedback") is True
