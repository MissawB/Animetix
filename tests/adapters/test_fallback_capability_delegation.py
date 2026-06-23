# tests/adapters/test_fallback_capability_delegation.py
from adapters.inference.capability_registry import CapabilityRegistry
from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.ports.inference_port import InferencePort


class _Base(InferencePort):
    def generate(self, *a, **k):
        return None

    def stream_generate(self, *a, **k):
        yield None

    def get_text_embedding(self, *a, **k):
        return []

    def health_check(self):
        return {"status": "offline"}


class _A(_Base):
    pass


class _B(_Base):
    pass


def test_adapter_exposes_capability_registry():
    fb = FallbackInferenceAdapter([_A(), _B()])
    assert isinstance(fb._capabilities, CapabilityRegistry)
    assert not hasattr(fb, "_capability_cache")
    assert not hasattr(fb, "_build_capability_cache")
    assert not hasattr(fb, "_is_method_overridden")


def test_generate_capability_routed_via_registry():
    a, b = _A(), _B()
    fb = FallbackInferenceAdapter([a, b])
    capable = fb._capabilities.for_method("generate")
    assert a in capable and b in capable


def test_set_primary_adapter_rebuilds_capabilities():
    a, b = _A(), _B()
    fb = FallbackInferenceAdapter([a, b])
    assert fb._capabilities.for_method("generate") == [a, b]
    assert fb.set_primary_adapter(1) is True
    assert fb._capabilities.for_method("generate") == [b, a]
