from unittest.mock import MagicMock

from adapters.inference.capability_registry import CapabilityRegistry
from core.ports.inference_port import InferencePort


class _Base(InferencePort):
    def generate(self, *a, **k):
        raise NotImplementedError

    def stream_generate(self, *a, **k):
        raise NotImplementedError

    def get_text_embedding(self, *a, **k):
        raise NotImplementedError

    def health_check(self):
        return {"status": "offline"}


class _Generic(_Base):
    pass  # does NOT override estimate_depth -> inherits the port default


class _Capable(_Base):
    def estimate_depth(self, image_data):
        return b"depth"


def test_is_method_overridden_true_for_override():
    assert CapabilityRegistry.is_method_overridden(_Capable(), "estimate_depth") is True


def test_is_method_overridden_false_for_port_default():
    assert (
        CapabilityRegistry.is_method_overridden(_Generic(), "estimate_depth") is False
    )


def test_is_method_overridden_ignores_mocks():
    assert (
        CapabilityRegistry.is_method_overridden(MagicMock(), "estimate_depth") is False
    )


def test_for_method_returns_only_capable_in_order():
    g, c = _Generic(), _Capable()
    reg = CapabilityRegistry([g, c])
    assert reg.for_method("estimate_depth") == [c]


def test_for_method_empty_when_none_capable():
    reg = CapabilityRegistry([_Generic()])
    assert reg.for_method("estimate_depth") == []


def test_rebuild_reflects_reordering():
    a, b = _Capable(), _Capable()
    reg = CapabilityRegistry([a, b])
    assert reg.for_method("estimate_depth") == [a, b]
    reg.rebuild([b, a])
    assert reg.for_method("estimate_depth") == [b, a]
