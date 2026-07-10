"""Regression locks for the User→Profile signal (2026-07-05 audit item).

The historical pair of receivers lived in ``models.py``: one created the
profile, the other re-saved it on EVERY ``User.save()`` (write amplification —
one extra full-profile UPDATE per login) and raised ``RelatedObjectDoesNotExist``
whenever the profile was missing (bulk-created/legacy users). The consolidated
receiver in ``signals.py`` must create on user creation, heal a missing profile
lazily, and never rewrite an existing one.
"""

import pytest
from animetix.models import Profile
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext

pytestmark = pytest.mark.django_db


def test_user_creation_creates_profile():
    user = User.objects.create_user(username="sig_create")
    assert Profile.objects.filter(user=user).exists()


def test_user_save_does_not_rewrite_profile():
    """Saving a user must not touch the profile row (write amplification)."""
    user = User.objects.create_user(username="sig_noamp")
    fresh = User.objects.get(pk=user.pk)

    with CaptureQueriesContext(connection) as ctx:
        fresh.save()

    profile_writes = [
        q["sql"]
        for q in ctx.captured_queries
        if "animetix_profile" in q["sql"]
        and q["sql"].lstrip().upper().startswith(("UPDATE", "INSERT"))
    ]
    assert profile_writes == [], f"user.save() wrote to the profile: {profile_writes}"


def test_user_save_heals_missing_profile():
    """Legacy/bulk-created users without a profile must not crash on save —
    the profile is (re)created instead of raising RelatedObjectDoesNotExist."""
    user = User.objects.create_user(username="sig_heal")
    Profile.objects.filter(user=user).delete()

    fresh = User.objects.get(pk=user.pk)
    fresh.save()  # must not raise

    assert Profile.objects.filter(user=fresh).exists()
