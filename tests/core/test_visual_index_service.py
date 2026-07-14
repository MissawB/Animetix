"""Une cible choisit son modèle ET sa collection — jamais l'un sans l'autre.

Le 12 juillet, des vecteurs écrits en 4096 dimensions ont été lus en 1024 : la
similarité rendait 0.0, sans jamais lever d'exception. Ce service existe pour
que ce couple ne puisse plus être dissocié.
"""

from unittest.mock import MagicMock

import pytest
from adapters.inference.ccip_vision import CCIP_MODEL_ID
from core.domain.exceptions import GameLogicError
from core.domain.services.visual_index import TARGETS, VisualIndexService


def _service():
    engine = MagicMock()
    engine.get_image_embedding.return_value = [0.1] * 512
    engine.get_text_embedding_clip.return_value = [0.2] * 512
    engine.get_character_embedding.return_value = [0.3] * 768
    repo = MagicMock()
    repo.get_collection_count.return_value = 0
    repo.search_by_vector.return_value = []
    return VisualIndexService(inference_engine=engine, repository=repo), engine, repo


def test_the_two_targets_are_the_ones_the_spec_fixed():
    assert TARGETS["work"].model_id == "dudcjs2779/anime-style-tag-clip"
    assert TARGETS["work"].collection == "unified_clip_space"
    assert set(TARGETS["work"].media_types) == {"Anime", "Manga", "Movie", "Game"}
    # La vraie constante CCIP, pas le nom du dépôt de base : `deepghs/ccip` ne
    # sert aucun graphe ONNX, seul `deepghs/ccip_onnx/...` est chargé en réalité.
    assert TARGETS["character"].model_id == CCIP_MODEL_ID
    assert TARGETS["character"].collection == "character_ccip_space"
    assert TARGETS["character"].media_types == ["Character"]


def test_a_work_image_is_encoded_by_the_work_model():
    service, engine, _ = _service()
    service.encode_image("work", b"png")
    engine.get_image_embedding.assert_called_once_with(
        b"png", model_id="dudcjs2779/anime-style-tag-clip"
    )
    engine.get_character_embedding.assert_not_called()


def test_a_character_image_is_encoded_by_ccip():
    service, engine, _ = _service()
    service.encode_image("character", b"png")
    engine.get_character_embedding.assert_called_once_with(b"png")
    engine.get_image_embedding.assert_not_called()


def test_a_search_only_ever_touches_its_own_target_collection():
    service, _, repo = _service()
    service.search("character", [0.3] * 768, limit=5)
    repo.search_by_vector.assert_called_once_with(
        "character_ccip_space", [0.3] * 768, limit=5
    )


def test_indexing_writes_under_external_id_and_into_the_target_collection():
    service, _, repo = _service()
    written = service.index(
        "work",
        [
            {
                "external_id": "38000",
                "media_type": "Anime",
                "title": "Kimetsu",
                "image": "u",
                "image_bytes": b"png",
            }
        ],
    )

    assert written == 1
    collection, ids, vectors, metadatas = repo.upsert_items.call_args[0]
    assert collection == "unified_clip_space"
    assert ids == ["38000"]  # l'id sous lequel le catalogue sert l'œuvre, pas un autre
    assert metadatas[0]["media_type"] == "Anime"
    assert metadatas[0]["title"] == "Kimetsu"


def test_text_search_is_refused_on_a_target_with_no_text_tower():
    # CCIP n'a pas d'encodeur de texte. Fusionner un vecteur de phrases générique
    # avec un vecteur CCIP donnerait un nombre qui a l'air juste et ne l'est pas.
    service, _, _ = _service()
    with pytest.raises(GameLogicError):
        service.encode_text("character", "une fille aux cheveux blancs")


def test_availability_is_asked_per_target():
    service, _, repo = _service()
    repo.get_collection_count.side_effect = lambda name: (
        12 if name == "unified_clip_space" else 0
    )

    assert service.is_available("work") is True
    assert service.is_available("character") is False


def test_an_unknown_target_is_refused():
    service, _, _ = _service()
    with pytest.raises(ValueError):
        service.encode_image("banana", b"png")
