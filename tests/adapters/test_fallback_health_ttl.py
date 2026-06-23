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


def test_recovered_adapter_rejoins_online_segment_after_ttl():
    clock = FakeClock()
    a = SpyAdapter("A", online=True)
    b = SpyAdapter("B", online=False)  # offline at init
    fb = FallbackInferenceAdapter([a, b], health_ttl=30.0, clock=clock)
    # At init, only A is online -> A first, B last.
    assert fb._get_ordered_adapters([a, b]) == [a, b]
    assert b not in fb._online_adapters

    b._online = True  # B recovers
    clock.advance(31.0)  # cross the TTL boundary
    ordered = fb._get_ordered_adapters([a, b])
    assert set(ordered[:2]) == {a, b}  # both online now
    assert b in fb._online_adapters


def test_failed_adapter_drops_to_offline_segment_after_ttl():
    clock = FakeClock()
    a = SpyAdapter("A", online=True)
    b = SpyAdapter("B", online=True)
    fb = FallbackInferenceAdapter([a, b], health_ttl=30.0, clock=clock)
    assert b in fb._online_adapters

    b._online = False  # B dies
    clock.advance(31.0)
    ordered = fb._get_ordered_adapters([a, b])
    assert ordered == [a, b]  # A (online) before B (offline)
    assert b not in fb._online_adapters


def test_public_health_check_is_cached_within_ttl():
    clock = FakeClock()
    a = SpyAdapter("A", online=True)
    fb = FallbackInferenceAdapter([a], health_ttl=30.0, clock=clock)
    assert a.health_calls == 1  # init probe
    result = fb.health_check()
    assert result["status"] == "online"
    assert result["adapters"] == [{"status": "online"}]
    # No extra probe within TTL.
    assert a.health_calls == 1


def test_public_health_check_reports_offline_when_all_offline():
    clock = FakeClock()
    a = SpyAdapter("A", online=False)
    fb = FallbackInferenceAdapter([a], health_ttl=30.0, clock=clock)
    result = fb.health_check()
    # Routing keeps A (safety net) but reported health is offline.
    assert result["status"] == "offline"
    assert a in fb._online_adapters
    # Cache holds within TTL: second call must not increase the probe count.
    probes_after_first_call = a.health_calls
    fb.health_check()
    assert a.health_calls == probes_after_first_call
    # The returned adapters list reflects the cached offline status.
    assert result["adapters"] == [{"status": "offline"}]
