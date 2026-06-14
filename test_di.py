import sys
from dependency_injector import containers, providers

class LazyClass:
    def __init__(self, module_name, class_name):
        self.module_name = module_name
        self.class_name = class_name
        self._class = None
    
    def __call__(self, *args, **kwargs):
        if self._class is None:
            import importlib
            module = importlib.import_module(self.module_name)
            self._class = getattr(module, self.class_name)
        return self._class(*args, **kwargs)

class Container(containers.DeclarativeContainer):
    # Pass some kwargs to test
    service = providers.Singleton(LazyClass("json", "dumps"), obj={"a": 1})

if __name__ == "__main__":
    if "json" in sys.modules:
        del sys.modules["json"]
    print("Container initialized. json module in sys.modules?", "json" in sys.modules)
    service = Container.service
    print("Service provider accessed. json module in sys.modules?", "json" in sys.modules)
    res = service()
    print("Service called. result:", res)
    print("json module in sys.modules?", "json" in sys.modules)
