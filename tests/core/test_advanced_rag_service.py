from unittest.mock import MagicMock

from core.domain.services.advanced_rag_service import AdvancedRAGService


def test_hybrid_search_is_lexical_only_no_vector_search():
    # Mesuré le 2026-07-15 sur les vrais vecteurs de prod : la « moitié
    # sémantique » CLIP rendait une proximité VISUELLE de jaquette, hors sujet
    # thématique, et DÉGRADAIT un top lexical impeccable en fusion. hybrid_search
    # est donc lexical seul. On verrouille qu'il n'appelle AUCUNE recherche
    # vectorielle sur le dépôt -- sinon on réintroduit le bruit qu'on vient de
    # retirer.
    repo = MagicMock()
    service = AdvancedRAGService(repo, MagicMock())
    idx = MagicMock()
    idx.search.return_value = [{"id": 1, "title": "Death Note"}]
    service._get_or_create_index = MagicMock(return_value=idx)
    service._adjust_scores_cognitively = lambda docs, q, user_id=None: docs

    results = service.hybrid_search("a dark psychological thriller", "Anime", limit=10)

    assert [r["title"] for r in results] == ["Death Note"]
    idx.search.assert_called_once_with("a dark psychological thriller", limit=10)
    repo.search_media_items.assert_not_called()
    repo.search_by_vector.assert_not_called()


def test_rag_colbert_filtering():
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    mock_colbert = MagicMock()

    # Simulate hybrid search returning 20 results
    mock_repo.load_catalog.return_value = {"db": []}

    service = AdvancedRAGService(mock_repo, mock_llm, colbert_adapter=mock_colbert)

    # Mock internal hybrid_search to return dummy docs
    dummy_docs = [{"id": i, "title": f"Doc {i}"} for i in range(20)]
    service.hybrid_search = MagicMock(return_value=dummy_docs)

    # Mock ColBERT to return top 5
    filtered_docs = dummy_docs[:5]
    for d in filtered_docs:
        d["colbert_score"] = 0.9
    mock_colbert.rank_documents.return_value = filtered_docs

    # Mock rerank_results
    service.rerank_results = MagicMock(return_value=filtered_docs)

    # Mock prompt_manager
    mock_prompt_mgr = MagicMock()
    mock_prompt_mgr.get_prompt.return_value = ("prompt", "sys")
    service.prompt_manager = mock_prompt_mgr

    service.generate_advanced_answer("test query", "Anime")

    # Verify ColBERT was called to filter down to 10 (or 5 in our mock) before rerank
    mock_colbert.rank_documents.assert_called_once_with("test query", dummy_docs)
    service.rerank_results.assert_called_once_with(
        "test query", filtered_docs, user_id=None
    )


def test_generate_holistic_answer():
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    mock_neo4j = MagicMock()
    mock_neo4j.get_community_summary.return_value = "This is a community summary."
    mock_prompt_mgr = MagicMock()
    mock_prompt_mgr.get_prompt.return_value = ("prompt", "sys")

    service = AdvancedRAGService(
        mock_repo, mock_llm, neo4j_manager=mock_neo4j, prompt_manager=mock_prompt_mgr
    )

    # Should use the community summary instead of normal vector search
    service.generate_holistic_answer("What is the main theme?", "Anime", "Shonen")

    mock_neo4j.get_community_summary.assert_called_once_with("Anime", "Shonen")
    mock_llm.inference_engine.generate.assert_called_once()
