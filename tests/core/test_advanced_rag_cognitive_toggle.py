from unittest.mock import MagicMock

from core.domain.services.advanced_rag_service import AdvancedRAGService


def _svc(enabled=True):
    return AdvancedRAGService(
        repository=MagicMock(),
        llm_service=MagicMock(),
        cognitive_boosters_enabled=enabled,
    )


def test_disabled_boosters_make_adjust_a_noop():
    svc = _svc(enabled=False)
    cands = [{"id": "1", "score": 0.5, "genres": ["shonen"]}]
    out = svc._adjust_scores_cognitively([dict(cands[0])], "shonen action")
    assert out == cands
    assert "cognitive_boost" not in out[0]


def test_enabled_boosters_apply_boost():
    svc = _svc(enabled=True)
    cands = [{"id": "1", "score": 0.5, "genres": ["shonen"]}]
    out = svc._adjust_scores_cognitively(cands, "shonen action")
    assert "cognitive_boost" in out[0]


def test_set_cognitive_boosters_flips_at_runtime():
    svc = _svc(enabled=True)
    svc.set_cognitive_boosters(False)
    cands = [{"id": "1", "score": 0.5, "genres": ["shonen"]}]
    out = svc._adjust_scores_cognitively([dict(cands[0])], "shonen")
    assert out == cands
