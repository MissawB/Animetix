from animetix.api.throttles import (
    BurstAnonRateThrottle,
    BurstUserRateThrottle,
    CpuGameThrottle,
)
from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle


def test_all_declared_scopes_have_a_rate():
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    for scope in ("anon", "user", "anon_burst", "user_burst", "cpu_game", "gpu"):
        assert scope in rates, f"missing rate for scope {scope}"
        assert rates[scope], f"empty rate for scope {scope}"


def test_burst_throttles_have_expected_scopes():
    assert BurstAnonRateThrottle.scope == "anon_burst"
    assert BurstUserRateThrottle.scope == "user_burst"
    assert CpuGameThrottle.scope == "cpu_game"


def test_burst_classes_are_in_default_throttle_classes():
    classes = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]
    assert "animetix.api.throttles.BurstAnonRateThrottle" in classes
    assert "animetix.api.throttles.BurstUserRateThrottle" in classes


def test_gpu_scoped_throttle_resolves_a_rate():
    # A view declaring throttle_scope="gpu" with ScopedRateThrottle must resolve
    # a concrete rate (the historical bug: scope declared but no rate → no-op).
    t = ScopedRateThrottle()
    t.scope = "gpu"
    assert t.get_rate() == "30/hour"
