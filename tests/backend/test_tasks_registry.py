from animetix.tasks_registry import get_registered_task, register_task


def test_registry_registration():
    @register_task("dummy_task")
    def dummy_func(x):
        return x * 2

    assert get_registered_task("dummy_task") == dummy_func
