from unittest.mock import MagicMock

from core.domain.exceptions import InferenceError
from core.domain.services.advanced_rag_service import AdvancedRAGService
from core.domain.services.rag.hybrid_index import HybridSearchIndex


def _rag_with_visual(visual):
    """Un service dont la moitié lexicale est mockée et l'ajustement cognitif neutralisé,
    pour isoler la fusion lexical + sémantique-CLIP."""
    service = AdvancedRAGService(MagicMock(), MagicMock(), visual_index_service=visual)
    idx = MagicMock()
    # La VRAIE fusion RRF -- c'est elle qu'on teste, pas un mock.
    idx.reciprocal_rank_fusion = HybridSearchIndex().reciprocal_rank_fusion
    service._get_or_create_index = MagicMock(return_value=idx)
    service._adjust_scores_cognitively = lambda docs, q, user_id=None: docs
    return service, idx


def test_hybrid_search_fuses_lexical_and_clip_on_the_mal_id_not_the_anilist_id():
    # Kimetsu : le catalogue lexical le connaît par son id AniList (101922), avec
    # idMal (38000) en second champ ; l'index CLIP (unified_clip_space) l'a écrit
    # sous external_id = MAL id (38000). Sans normalisation sur une clé commune,
    # RRF verrait DEUX œuvres (101922 et 38000) et n'en renforcerait aucune. On
    # prouve qu'il n'en voit qu'UNE, clavetée sur le MAL id.
    visual = MagicMock()
    visual.encode_text.return_value = [0.1, 0.2, 0.3]
    visual.search.return_value = [
        {
            "id": "38000",
            "external_id": "38000",
            "media_type": "Anime",
            "title": "Kimetsu no Yaiba",
        }
    ]
    service, idx = _rag_with_visual(visual)
    idx.search.return_value = [
        {"id": 101922, "idMal": 38000, "title": "Kimetsu no Yaiba"}
    ]

    results = service.hybrid_search("demon slayer", "Anime", limit=10)

    kimetsu = [r for r in results if r.get("title") == "Kimetsu no Yaiba"]
    assert len(kimetsu) == 1, f"attendu 1 entrée fusionnée, obtenu {len(kimetsu)}"
    assert str(kimetsu[0]["id"]) == "38000"


def test_hybrid_search_encodes_with_clip_text_tower_and_filters_by_media_type():
    visual = MagicMock()
    visual.encode_text.return_value = [0.1, 0.2, 0.3]
    visual.search.return_value = []
    service, idx = _rag_with_visual(visual)
    idx.search.return_value = []

    service.hybrid_search("une fille aux cheveux blancs", "Anime", limit=10)

    visual.encode_text.assert_called_once_with("work", "une fille aux cheveux blancs")
    args, kwargs = visual.search.call_args
    assert args[0] == "work"
    assert kwargs.get("where") == {"media_type": "Anime"}


def test_hybrid_search_degrades_to_lexical_when_clip_fails():
    # Chemin FACTURÉ (agentic-rag, 6 Bx) : un brain froid ne doit pas faire 500,
    # juste retomber sur le lexical.
    visual = MagicMock()
    visual.encode_text.side_effect = InferenceError("brain froid")
    service, idx = _rag_with_visual(visual)
    idx.search.return_value = [{"id": 101922, "idMal": 38000, "title": "Kimetsu"}]

    results = service.hybrid_search("demon slayer", "Anime", limit=10)

    assert [r.get("title") for r in results] == ["Kimetsu"]
    visual.search.assert_not_called()


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
