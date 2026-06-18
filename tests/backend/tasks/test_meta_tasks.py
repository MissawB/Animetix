import pytest
from animetix.tasks.meta_tasks import scheduled_dpo_optimization


@pytest.mark.django_db
def test_scheduled_dpo_optimization_already_running(mocker):
    mock_cache = mocker.patch("django.core.cache.cache.add")
    mock_cache.return_value = False

    res = scheduled_dpo_optimization()
    assert res == "Task already running."
    mock_cache.assert_called_once_with("scheduled_dpo_optimization_lock", "true", 3600)


@pytest.mark.django_db
def test_scheduled_dpo_optimization_no_feedbacks(mocker):
    mocker.patch("django.core.cache.cache.add", return_value=True)
    mock_delete = mocker.patch("django.core.cache.cache.delete")

    # Mock AIFeedback.objects.filter...
    mock_filter = mocker.patch("animetix.models.AIFeedback.objects.filter")
    mock_filter.return_value.values.return_value.annotate.return_value.filter.return_value = (
        []
    )

    res = scheduled_dpo_optimization()
    assert res == "No prompts needed optimization today."
    mock_delete.assert_called_once_with("scheduled_dpo_optimization_lock")
