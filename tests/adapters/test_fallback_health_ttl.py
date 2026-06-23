"""TTL cache for FallbackInferenceAdapter health checks.

Health is re-probed at most once per TTL window. Routing (`_online_adapters`)
and the public `health_check()` both read the cached state. Uses real
InferencePort subclasses (not mocks) and an injectable monotonic clock.
"""

from adapters.inference.fallback_adapter import FallbackInferenceAdapter
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferencePort


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class SpyAdapter(InferencePort):
    """Real InferencePort subclass that counts health probes and can flip
    online/offline between probes."""

    def __init__(self, name="Spy", online=True):
        super().__init__()
        self._name = name
        self._online = online
        self.health_calls = 0

    def health_check(self) -> dict:
        self.health_calls += 1
        return {"status": "online" if self._online else "offline"}

    def generate(self, prompt, system_prompt="sys", **kwargs):  # pragma: no cover
        return InferenceResponse(text="ok")

    def stream_generate(
        self, prompt, system_prompt="sys", **kwargs
    ):  # pragma: no cover
        raise NotImplementedError

    def get_text_embedding(self, text):  # pragma: no cover
        raise NotImplementedError


def test_refresh_is_cached_within_ttl():
    clock = FakeClock()
    a = SpyAdapter("A", online=True)
    fb = FallbackInferenceAdapter([a], health_ttl=30.0, clock=clock)
    # __init__ forced one probe.
    assert a.health_calls == 1
    # Within TTL: no re-probe.
    fb._refresh_health_if_stale()
    assert a.health_calls == 1


def test_refresh_reprobes_after_ttl():
    clock = FakeClock()
    a = SpyAdapter("A", online=True)
    fb = FallbackInferenceAdapter([a], health_ttl=30.0, clock=clock)
    clock.advance(31.0)
    fb._refresh_health_if_stale()
    assert a.health_calls == 2


def test_health_ttl_defaults_to_30_without_env(monkeypatch):
    monkeypatch.delenv("FALLBACK_HEALTH_TTL_SECONDS", raising=False)
    fb = FallbackInferenceAdapter([SpyAdapter("A")])
    assert fb._health_ttl == 30.0


def test_health_ttl_reads_env(monkeypatch):
    monkeypatch.setenv("FALLBACK_HEALTH_TTL_SECONDS", "5")
    fb = FallbackInferenceAdapter([SpyAdapter("A")])
    assert fb._health_ttl == 5.0


def test_all_offline_allows_all_adapters():
    clock = FakeClock()
    a = SpyAdapter("A", online=False)
    b = SpyAdapter("B", online=False)
    fb = FallbackInferenceAdapter([a, b], health_ttl=30.0, clock=clock)
    # Safety net: every adapter offline -> all kept online for routing.
    assert fb._online_adapters == {a, b}
