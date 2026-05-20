import pytest
from unittest.mock import MagicMock
import numpy as np
from core.domain.services.advanced_rag_service import AdvancedRAGService

@pytest.fixture
def mock_repository():
    repo = MagicMock()
    # On met plus de contenu pour aider le vectorizer TF-IDF
    repo.load_catalog.return_value = {
        'db': [
            {'id': '1', 'title': 'Naruto', 'description': 'Naruto is a shinobi ninja from the leaf village. He wants to be Hokage.', 'genres': ['Action']},
            {'id': '2', 'title': 'One Piece', 'description': 'Luffy is a pirate who wants to find the One Piece treasure in the grand sea.', 'genres': ['Adventure']}
        ]
    }
    return repo

@pytest.fixture
def mock_llm_service():
    service = MagicMock()
    service.inference_engine.generate.return_value = "OUI"
    # Ajout d'un mock pour prompt_manager pour éviter les erreurs d'unpacking
    pm = MagicMock()
    pm.get_prompt.return_value = ("Test Prompt", "System Prompt")
    service.prompt_manager = pm
    return service

@pytest.fixture
def rag_service(mock_repository, mock_llm_service):
    return AdvancedRAGService(repository=mock_repository, llm_service=mock_llm_service)

def test_hybrid_search(rag_service):
    # La recherche hybride initialise l'index automatiquement au premier appel
    # On utilise un mot qui est CLAIREMENT dans le texte
    results = rag_service.hybrid_search("ninja", "Anime", limit=1)
    
    assert len(results) >= 1
    assert "Naruto" in results[0]['title']

def test_rerank_results_no_reranker(rag_service):
    candidates = [{'id': '1', 'title': 'A'}, {'id': '2', 'title': 'B'}]
    assert rag_service.rerank_results("query", candidates) == candidates

def test_rerank_results_with_mock_reranker(rag_service):
    mock_reranker = MagicMock()
    mock_reranker.predict.return_value = np.array([0.1, 0.9])
    rag_service.reranker = mock_reranker
    
    candidates = [{'id': '1', 'title': 'A'}, {'id': '2', 'title': 'B'}]
    ranked = rag_service.rerank_results("query", candidates)
    
    assert ranked[0]['title'] == 'B' # Higher score
    assert ranked[1]['title'] == 'A'

def test_self_rag_verify(rag_service, mock_llm_service):
    assert rag_service.self_rag_verify("query", "context") is True
    
    mock_llm_service.inference_engine.generate.return_value = "NON"
    assert rag_service.self_rag_verify("query", "context") is False

def test_generate_advanced_answer(rag_service, mock_llm_service):
    mock_llm_service.inference_engine.generate.return_value = "The answer is Naruto."
    ans = rag_service.generate_advanced_answer("Who is Naruto?", "Anime")
    assert "Naruto" in ans
