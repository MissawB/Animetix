"""Behavior tests for ``adapters.persistence.django_safety_adapter``.

The adapter is a Django-ORM-backed implementation of ``SafetyPort``: it writes
guardrail events to ``AISafetyEvent`` and reads aggregate stats / recent events
back out.

We patch the ``AISafetyEvent`` and ``User`` models *in the module namespace* so
``.objects.create/get/filter/all/count`` become MagicMocks. This keeps the test a
fast, isolated unit (no DB, no async/DB pollution of the shared suite) while still
asserting the REAL adapter logic: the kwargs/filters it builds, the user-lookup
branch, the health-score formula, the category distribution, and the
row -> dict / snippet-truncation mapping.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import adapters.persistence.django_safety_adapter as mod
import pytest
from adapters.persistence.django_safety_adapter import DjangoSafetyAdapter

# --- helpers -------------------------------------------------------------


def _event_row(
    *,
    eid=1,
    created_at=None,
    event_type="input",
    action_taken="block",
    detected_categories=None,
    input_text="hi",
    reasoning="because",
):
    """A lightweight stand-in for an AISafetyEvent row (only attrs the
    adapter touches)."""
    return SimpleNamespace(
        id=eid,
        created_at=created_at or datetime(2026, 6, 20, 12, 0, 0),
        event_type=event_type,
        action=action_taken,  # model attribute is `action`
        detected_categories=detected_categories or [],
        input_text=input_text,
        reasoning=reasoning,
    )


# --- log_safety_event ----------------------------------------------------


def test_log_event_without_user_passes_none_and_defaults(mocker):
    model = mocker.patch.object(mod, "AISafetyEvent")
    user_model = mocker.patch.object(mod, "User")
    created = object()
    model.objects.create.return_value = created

    result = DjangoSafetyAdapter().log_safety_event(
        event_type="input",
        action_taken="block",
        # detected_categories left None -> must become []
        input_text="in",
        output_text="out",
        reasoning="why",
    )

    # Returns exactly what the ORM create() returned.
    assert result is created
    # No user_id -> User lookup must NOT happen.
    user_model.objects.get.assert_not_called()
    model.objects.create.assert_called_once_with(
        user=None,
        event_type="input",
        action="block",  # model field is `action`, not `action_taken`
        detected_categories=[],  # None coalesced to empty list
        input_text="in",
        output_text="out",
        reasoning="why",
    )


def test_log_event_with_valid_user_looks_up_and_attaches(mocker):
    model = mocker.patch.object(mod, "AISafetyEvent")
    user_model = mocker.patch.object(mod, "User")
    fake_user = SimpleNamespace(id=7)
    user_model.objects.get.return_value = fake_user

    DjangoSafetyAdapter().log_safety_event(
        event_type="output",
        action_taken="warn",
        detected_categories=["violence", "hate"],
        user_id=7,
    )

    # User looked up by the given id.
    user_model.objects.get.assert_called_once_with(id=7)
    _, kwargs = model.objects.create.call_args
    assert kwargs["user"] is fake_user
    # Provided categories are passed through unchanged.
    assert kwargs["detected_categories"] == ["violence", "hate"]
    # Unspecified text fields default to empty strings (not None).
    assert kwargs["input_text"] == ""
    assert kwargs["output_text"] == ""


def test_log_event_missing_user_falls_back_to_none(mocker):
    """If the user_id does not resolve, the event is still created with user=None."""
    model = mocker.patch.object(mod, "AISafetyEvent")
    user_model = mocker.patch.object(mod, "User")

    # Real DoesNotExist semantics: adapter catches User.DoesNotExist.
    class DoesNotExist(Exception):
        pass

    user_model.DoesNotExist = DoesNotExist
    user_model.objects.get.side_effect = DoesNotExist()

    DjangoSafetyAdapter().log_safety_event(
        event_type="input",
        action_taken="none",
        user_id=999,
    )

    user_model.objects.get.assert_called_once_with(id=999)
    _, kwargs = model.objects.create.call_args
    assert kwargs["user"] is None


# --- get_safety_stats ----------------------------------------------------


def test_get_safety_stats_aggregates_and_scores(mocker):
    model = mocker.patch.object(mod, "AISafetyEvent")

    # filter(action_taken__in=[...]).count() -> blocked count
    blocked_qs = MagicMock()
    blocked_qs.count.return_value = 3
    model.objects.filter.return_value = blocked_qs
    # objects.count() -> total events
    model.objects.count.return_value = 200
    # objects.all() iterated for category distribution
    model.objects.all.return_value = [
        _event_row(detected_categories=["violence", "hate"]),
        _event_row(detected_categories=["violence"]),
        _event_row(detected_categories=[]),
    ]

    stats = DjangoSafetyAdapter().get_safety_stats()

    # Correct filter built for "blocked" actions.
    model.objects.filter.assert_called_once_with(action__in=["block", "rewrite"])

    assert stats["total_violations"] == 200
    assert stats["blocked_count"] == 3
    assert stats["category_distribution"] == {"violence": 2, "hate": 1}
    # Formula: round((1 - blocked / max(1, total/100)) * 100, 1)
    #        = round((1 - 3 / (200/100)) * 100, 1) = round((1 - 1.5) * 100, 1) = -50.0
    assert stats["safety_health_score"] == -50.0


def test_get_safety_stats_guards_zero_total(mocker):
    """With no events, max(1, 0/100) prevents division-by-zero and yields 100.0."""
    model = mocker.patch.object(mod, "AISafetyEvent")
    blocked_qs = MagicMock()
    blocked_qs.count.return_value = 0
    model.objects.filter.return_value = blocked_qs
    model.objects.count.return_value = 0
    model.objects.all.return_value = []

    stats = DjangoSafetyAdapter().get_safety_stats()

    assert stats["total_violations"] == 0
    assert stats["blocked_count"] == 0
    assert stats["category_distribution"] == {}
    # (1 - 0 / max(1, 0)) * 100 = 100.0
    assert stats["safety_health_score"] == 100.0


# --- get_recent_events ---------------------------------------------------


def test_get_recent_events_orders_limits_and_maps(mocker):
    model = mocker.patch.object(mod, "AISafetyEvent")

    long_input = "x" * 250
    short_input = "short"
    rows = [
        _event_row(
            eid=1,
            created_at=datetime(2026, 6, 20, 9, 30, 0),
            event_type="input",
            action_taken="block",
            detected_categories=["violence"],
            input_text=long_input,
            reasoning="r1",
        ),
        _event_row(
            eid=2,
            created_at=datetime(2026, 6, 20, 8, 0, 0),
            event_type="output",
            action_taken="warn",
            detected_categories=[],
            input_text=short_input,
            reasoning="r2",
        ),
    ]

    # all().order_by("-created_at")[:limit] -> rows
    sliced = MagicMock()
    sliced.__getitem__.return_value = rows
    ordered = MagicMock()
    ordered.order_by.return_value = sliced
    model.objects.all.return_value = ordered

    out = DjangoSafetyAdapter().get_recent_events(limit=10)

    # Ordering by newest-first was requested.
    ordered.order_by.assert_called_once_with("-created_at")
    # The limit was applied as a slice [:10].
    sl = sliced.__getitem__.call_args[0][0]
    assert isinstance(sl, slice) and sl.stop == 10

    assert len(out) == 2

    first = out[0]
    assert first["id"] == 1
    assert first["timestamp"] == "2026-06-20T09:30:00"
    assert first["event_type"] == "input"
    assert first["action"] == "block"
    assert first["categories"] == ["violence"]
    assert first["reasoning"] == "r1"
    # Long input is truncated to 100 chars + "..."
    assert first["input_snippet"] == "x" * 100 + "..."

    second = out[1]
    # Short input is left intact (no ellipsis).
    assert second["input_snippet"] == "short"
    assert second["action"] == "warn"


def test_get_recent_events_default_limit_is_50(mocker):
    model = mocker.patch.object(mod, "AISafetyEvent")
    sliced = MagicMock()
    sliced.__getitem__.return_value = []
    ordered = MagicMock()
    ordered.order_by.return_value = sliced
    model.objects.all.return_value = ordered

    out = DjangoSafetyAdapter().get_recent_events()

    assert out == []
    sl = sliced.__getitem__.call_args[0][0]
    assert isinstance(sl, slice) and sl.stop == 50


# --- real-DB regression lock --------------------------------------------------


@pytest.mark.django_db
def test_log_safety_event_real_db_roundtrip():
    """Round-trips against the real ORM, unlike the mocked tests above.

    This is the test that catches model/adapter field mismatches: the adapter
    previously wrote ``action_taken=`` / filtered ``action_taken__in`` / read
    ``e.action_taken`` while the ``AISafetyEvent`` model field is ``action`` —
    which raises ``TypeError``/``FieldError`` against a real database.
    """
    adapter = DjangoSafetyAdapter()

    row = adapter.log_safety_event(
        event_type="input",
        action_taken="block",
        detected_categories=["violence"],
        input_text="hello",
        output_text="bye",
        reasoning="why",
    )
    assert row.pk is not None
    assert row.action == "block"  # written to the real `action` column

    # Aggregate query (filter action__in=...) runs for real.
    stats = adapter.get_safety_stats()
    assert stats["total_violations"] == 1
    assert stats["blocked_count"] == 1

    # Recent-events mapping reads e.action for real.
    recent = adapter.get_recent_events()
    assert recent[0]["action"] == "block"
    assert recent[0]["categories"] == ["violence"]
