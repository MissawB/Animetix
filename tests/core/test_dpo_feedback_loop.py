from unittest.mock import MagicMock, patch

import pytest
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop


@pytest.fixture
def dpo_loop(tmp_path):
    from adapters.persistence.django_feedback_adapter import (  # noqa: E402
        DjangoFeedbackAdapter,
    )

    return DPOFeedbackLoop(
        data_dir=str(tmp_path), feedback_port=DjangoFeedbackAdapter()
    )


@pytest.mark.django_db
def test_export_preference_dataset(dpo_loop, tmp_path):
    from animetix.models import AIFeedback  # noqa: E402

    # Setup mock data in DB
    AIFeedback.objects.create(input_context="q", output_text="r", is_positive=True)

    # We mock open only for this test, correctly
    with patch("builtins.open", MagicMock()):
        # Let's just run it and check if it doesn't crash
        # The actual file writing is handled by the mock
        dpo_loop.export_preference_dataset()


@pytest.mark.django_db
def test_analyze_feedback_trends(dpo_loop):
    from animetix.models import AIFeedback  # noqa: E402

    AIFeedback.objects.create(input_context="fail", is_positive=False)
    AIFeedback.objects.create(input_context="ok", is_positive=True)

    trends = dpo_loop.analyze_feedback_trends()
    assert trends["satisfaction_rate"] == 50.0
    assert len(trends["top_failures"]) == 1
    assert trends["top_failures"][0]["input_context"] == "fail"
