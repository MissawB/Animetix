import pytest
from adapters.inference.lazy_local_model_adapter import LazyLocalModelAdapter
from core.domain.exceptions import InferenceError


class _Fake(LazyLocalModelAdapter):
    ENGINE_NAME = "fake"

    def __init__(self, fail=False):
        super().__init__()
        self.model = None
        self._loads = 0
        self._fail = fail

    def _load_model_impl(self):
        self._loads += 1
        if self._fail:
            raise RuntimeError("boom")
        self.model = object()

    # satisfy the remaining InferencePort abstract methods
    def generate(self, *a, **k): ...

    def stream_generate(self, *a, **k): ...

    def get_text_embedding(self, *a, **k): ...


def test_load_model_calls_impl_when_not_loaded():
    f = _Fake()
    f._load_model()
    assert f._loads == 1 and f.model is not None


def test_load_model_noop_when_loaded():
    f = _Fake()
    f._load_model()
    f._load_model()
    assert f._loads == 1


def test_load_model_wraps_failure_in_inference_error():
    f = _Fake(fail=True)
    with pytest.raises(
        InferenceError, match="Critical failure during fake model loading: boom"
    ):
        f._load_model()
    assert f.model is None  # stays unset so a retry is possible


def test_health_check_offline_then_online():
    f = _Fake()
    assert f.health_check() == {"status": "offline", "engine": "fake"}
    f._load_model()
    assert f.health_check() == {"status": "online", "engine": "fake"}


def test_is_ready_override_is_independent_of_lazy_load_guard():
    class _ReadyFake(_Fake):
        def _is_ready(self):
            return True

    f = _ReadyFake()
    # health uses _is_ready -> online even though the model is not loaded
    assert f.health_check()["status"] == "online"
    # the lazy-load guard uses _is_loaded (model is None) -> still loads
    f._load_model()
    assert f._loads == 1
