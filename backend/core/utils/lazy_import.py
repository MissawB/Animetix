"""lazy_import.py – Helper to lazily import optional heavy dependencies.

Usage::

    from core.utils.lazy_import import lazy_import  # noqa: E402
    torch = lazy_import('torch')
    # ``torch`` is imported on first attribute access. If the module is not
    # installed, an ImportError with a clear message is raised.
"""

import importlib  # noqa: E402
from types import ModuleType  # noqa: E402
from typing import Any  # noqa: E402

_lazy_cache = {}
_loaded_modules = {}


def lazy_import(module_name: str) -> ModuleType:
    """Return a proxy object that lazily imports *module_name*.

    The returned object mimics a module; attribute access triggers the real
    import. If the module cannot be imported, an ImportError is raised with a
    helpful suggestion to install the optional dependency.
    """
    if module_name in _lazy_cache:
        return _lazy_cache[module_name]

    class _LazyModule(ModuleType):
        def __init__(self):
            super().__init__(module_name)
            self._loading = False

        def _load(self) -> ModuleType:
            if module_name not in _loaded_modules:
                if self._loading:
                    raise AttributeError("Re-entrant load")
                self._loading = True
                try:
                    real_module = importlib.import_module(module_name)
                    _loaded_modules[module_name] = real_module
                except ImportError as exc:
                    raise ImportError(
                        f"Optional dependency '{module_name}' is required for this "
                        f"functionality but is not installed. Install it via "
                        f"'pip install {module_name}' or add it to the project's "
                        f"optional dependencies."
                    ) from exc
                finally:
                    self._loading = False
            return _loaded_modules[module_name]

        @property
        def __spec__(self) -> Any:
            if self._loading:
                return None
            try:
                return self._load().__spec__
            except ImportError:
                return None

        @property
        def __file__(self) -> Any:
            if module_name in _loaded_modules:
                return getattr(_loaded_modules[module_name], "__file__", None)
            return None

        @property
        def __path__(self) -> Any:
            if module_name in _loaded_modules:
                return getattr(_loaded_modules[module_name], "__path__", None)
            return []

        @property
        def __loader__(self) -> Any:
            if module_name in _loaded_modules:
                return getattr(_loaded_modules[module_name], "__loader__", None)
            return None

        @property
        def __package__(self) -> Any:
            if module_name in _loaded_modules:
                return getattr(_loaded_modules[module_name], "__package__", None)
            return None

        def __getattr__(self, item: str) -> Any:
            if item.startswith("__") and item.endswith("__"):
                if item == "__path__":
                    return []
                raise AttributeError(item)
            return getattr(self._load(), item)

        def __dir__(self):  # pragma: no cover – helps REPL auto‑completion
            return dir(self._load())

    proxy = _LazyModule()
    _lazy_cache[module_name] = proxy
    return proxy
