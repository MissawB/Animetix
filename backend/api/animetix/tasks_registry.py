TASK_REGISTRY = {}


def register_task(name):
    def decorator(func):
        TASK_REGISTRY[name] = func
        return func

    return decorator


def get_registered_task(name):
    return TASK_REGISTRY.get(name)
