"""Transparency dashboard endpoint — verifies it is wired to real data."""

import pytest
from animetix.models import AIFeedback, AIREvalResult, AISafetyEvent
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_transparency_empty_db_is_safe(api_client):
    """Public endpoint must never 500, even with no data, and expose the
    canonical benchmark list + drift keys instead of leaving them empty."""
    resp = api_client.get(reverse("api_transparency"))
    assert resp.status_code == 200, resp.content
    data = resp.json()

    assert data["status"] == "synchronized"
    gm = data["global_metrics"]
    assert gm["total_feedbacks"] == 0
    assert gm["community_satisfaction"] == 0.0
    assert gm["model_version"]  # declared label, always present
    # No evals yet → reliability/last_training unknown (front applies fallbacks).
    assert data["model_uptime"] is None
    assert gm["last_training"] is None
    assert data["evolution_timeline"] == []
    # Benchmarks come from the canonical curated service (never empty).
    assert len(data["sota_benchmarks"]) > 0
    assert "elo_score" in data["sota_benchmarks"][0]
    # Drift is a dict (real KS service; "unknown" without baselines).
    assert isinstance(data["embedding_drift"], dict)
    # The fabricated bias metric is gone.
    assert "bias_score" not in data["ethics_audit"]
    assert data["ethics_audit"]["hallucination_rate"] == 0.0


@pytest.mark.django_db
def test_transparency_reflects_real_data(api_client):
    # 4 feedbacks, 3 positive → satisfaction 0.75
    for is_pos in (True, True, True, False):
        AIFeedback.objects.create(is_positive=is_pos)

    # 5 evals, 1 hallucination → hallucination_rate 0.2, reliability 80%
    for i in range(5):
        AIREvalResult.objects.create(
            faithfulness=0.9,
            relevancy=0.8,
            precision=0.7,
            hallucination_detected=(i == 0),
        )

    # Safety: 2 blocked over 5 evaluated interactions → compliance 0.6
    AISafetyEvent.objects.create(event_type="output", action="block")
    AISafetyEvent.objects.create(event_type="output", action="rewrite")
    AISafetyEvent.objects.create(event_type="input", action="none")

    resp = api_client.get(reverse("api_transparency"))
    assert resp.status_code == 200
    data = resp.json()

    gm = data["global_metrics"]
    assert gm["total_feedbacks"] == 4
    assert gm["community_satisfaction"] == 0.75
    assert data["ethics_audit"]["hallucination_rate"] == 0.2
    assert data["model_uptime"] == 80.0
    assert data["ethics_audit"]["safety_compliance"] == 0.6
    # ethics_score = mean(1-halluc=0.8, satisfaction=0.75, compliance=0.6) * 100
    assert data["ethics_score"] == pytest.approx(71.7, abs=0.1)
    # One month of evals → one timeline point.
    assert len(data["evolution_timeline"]) == 1
    assert 0.0 <= data["evolution_timeline"][0]["accuracy"] <= 1.0
    assert gm["last_training"] is not None
