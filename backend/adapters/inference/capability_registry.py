import inspect
import logging
from typing import Dict, List

from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.capability_registry")


class CapabilityRegistry:
    """Detects which adapters override which InferencePort methods, and caches it.

    The detection is class-based (an adapter "has" a capability iff its class
    overrides the corresponding InferencePort method), moved verbatim out of
    FallbackInferenceAdapter.
    """

    def __init__(self, adapters: List[InferencePort]):
        self._cache: Dict[str, List[InferencePort]] = {}
        self.rebuild(adapters)

    def for_method(self, method_name: str) -> List[InferencePort]:
        """Adapters that override `method_name`, in adapter order; [] if none."""
        return self._cache.get(method_name, [])

    def rebuild(self, adapters: List[InferencePort]) -> None:
        """Rebuild the cache from the given adapter list (order preserved)."""
        port_methods = [
            name
            for name, _val in inspect.getmembers(
                InferencePort, predicate=inspect.isfunction
            )
            if not name.startswith("_")
        ]
        self._cache = {}
        for method_name in port_methods:
            capable = [
                adapter
                for adapter in adapters
                if self.is_method_overridden(adapter, method_name)
            ]
            self._cache[method_name] = capable
            logger.debug(
                f"⚙️ [CapabilityRegistry] '{method_name}': "
                f"{[a.__class__.__name__ for a in capable]}"
            )

    @staticmethod
    def is_method_overridden(adapter: InferencePort, method_name: str) -> bool:
        # Ignore mock objects to avoid registering instance-level mock methods.
        if getattr(adapter.__class__, "__module__", "") == "unittest.mock" or hasattr(
            adapter, "mock_calls"
        ):
            return False

        cls = adapter.__class__
        method = getattr(cls, method_name, None)
        if method is None or not callable(method):
            return False

        port_method = getattr(InferencePort, method_name, None)
        if port_method is None:
            return True

        adapter_func = getattr(method, "__func__", method)
        port_func = getattr(port_method, "__func__", port_method)
        return adapter_func is not port_func
