import logging

import pytest
from adapters.inference.lazy_load_mixin import LazyLoadMixin
from core.domain.exceptions import InferenceError


class _Fake(LazyLoadMixin):
    def __init__(self):
        self.attr = None
        self._loads = 0

    def _good(self):
        self._loads += 1
        self.attr = object()

    def _bad(self):
        self._loads += 1
        raise RuntimeError("boom")


def test_lazy_load_calls_loader_when_not_loaded():
    f = _Fake()
    f._lazy_load("attr", f._good, label="thing")
    assert f._loads == 1 and f.attr is not None


def test_lazy_load_noop_when_already_loaded():
    f = _Fake()
    f.attr = object()
    f._lazy_load("attr", f._good, label="thing")
    assert f._loads == 0


def test_lazy_load_swallows_failure_by_default(caplog):
    f = _Fake()
    with caplog.at_level(logging.ERROR):
        f._lazy_load("attr", f._bad, label="thing")  # must NOT raise
    assert f.attr is None  # stays unset so a retry is possible
    assert "Failed to load thing" in caplog.text


def test_lazy_load_raises_when_on_error_raise():
    f = _Fake()
    with pytest.raises(
        InferenceError, match="Critical failure during thing model loading: boom"
    ):
        f._lazy_load("attr", f._bad, label="thing", on_error="raise")
