from unittest.mock import MagicMock

from core.domain.services.advanced_rag_service import AdvancedRAGService


def _svc():
    s = AdvancedRAGService(repository=MagicMock(), llm_service=MagicMock())
    s.colbert_adapter = None
    s.prompt_manager = MagicMock()
    s.prompt_manager.get_prompt.return_value = ("p", "s")
    s.llm_service.inference_engine.generate.return_value = MagicMock(text="ANSWER")
    s.hybrid_search = MagicMock(
        return_value=[{"id": "1", "title": "Naruto", "description": "ninja boy"}]
    )
    s.rerank_results = MagicMock(
        return_value=[{"id": "1", "title": "Naruto", "description": "ninja boy"}]
    )
    return s


def test_with_context_returns_answer_and_context():
    svc = _svc()
    answer, context = svc.generate_advanced_answer_with_context("q", "Anime")
    assert answer == "ANSWER"
    assert "Naruto" in context


def test_generate_advanced_answer_returns_only_answer():
    svc = _svc()
    svc.generate_advanced_answer_with_context = MagicMock(return_value=("A", "ctx"))
    assert svc.generate_advanced_answer("q", "Anime") == "A"
