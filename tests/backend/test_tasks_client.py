import pytest
from django.core.cache import cache
from animetix.tasks_client import enqueue_task
from animetix.tasks_registry import register_task


@pytest.fixture(autouse=True)
def cleanup_cache():
    cache.clear()


def test_enqueue_task_eager_local(settings):
    settings.IS_PRODUCTION = False

    @register_task("test_eager_task")
    def sample_task(x, y):
        return x + y

    task_id = enqueue_task("test_eager_task", 10, y=20)
    assert task_id is not None

    # Verify execution state saved in cache
    result = cache.get(f"task_result:{task_id}")
    assert result is not None
    assert result["ready"] is True
    assert result["result"] == 30
