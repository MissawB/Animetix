"""Une cible choisit son modèle ET sa collection — jamais l'un sans l'autre.

Le 12 juillet, des vecteurs écrits en 4096 dimensions ont été lus en 1024 : la
similarité rendait 0.0, sans jamais lever d'exception. Ce service existe pour
que ce couple ne puisse plus être dissocié.

Deux règles de test, apprises la même semaine :

1. Les doublures sont construites avec `spec=` sur les VRAIS ports. Un
   `MagicMock()` nu répond à n'importe quel nom d'attribut : il aurait laissé
   passer un service qui appelle `repository.search_by_vector` — méthode qui
   n'existe sur AUCUN dépôt réel — et les tests seraient restés verts pendant
   que la fonctionnalité levait `AttributeError` en production.
2. Le câblage lui-même est testé contre les vraies classes (voir la section
   « contrat »). Une doublure, même bien spécifiée, ne dit rien de ce que le
   conteneur injecte réellement.
"""

import importlib
from unittest.mock import MagicMock

import pytest
from core.domain.exceptions import GameLogicError, InferenceError
from core.domain.services.visual_index import TARGETS, VisualIndexService
from core.ports.inference_port import InferencePort
from core.ports.repository_port import RepositoryPort
from core.ports.vector_store_port import VectorStorePort
from core.utils.model_registry import ANIME_CLIP_MODEL_ID, CCIP_MODEL_ID


def _service():
    engine = MagicMock(spec=InferencePort)
    engine.get_image_embedding.return_value = [0.1] * 512
    engine.get_text_embedding_clip.return_value = [0.2] * 512
    engine.get_character_embedding.return_value = [0.3] * 768

    repo = MagicMock(spec=RepositoryPort)

    store = MagicMock(spec=VectorStorePort)
    store.get_collection_count.return_value = 0
    store.search_by_vector.return_value = []

    service = VisualIndexService(
        inference_engine=engine, repository=repo, vector_store=store
    )
    return service, engine, repo, store


def test_the_two_targets_are_the_ones_the_spec_fixed():
    assert TARGETS["work"].model_id == "dudcjs2779/anime-style-tag-clip"
    assert TARGETS["work"].collection == "unified_clip_space"
    assert set(TARGETS["work"].media_types) == {"Anime", "Manga", "Movie", "Game"}
    # La vraie constante CCIP : `deepghs/ccip` est le dépôt de base (checkpoints
    # torch), il ne sert aucun graphe ONNX. Nommer un modèle que personne ne
    # charge, c'est la même panne silencieuse sous un autre nom.
    assert TARGETS["character"].model_id == CCIP_MODEL_ID
    assert CCIP_MODEL_ID == "deepghs/ccip_onnx/ccip-caformer-24-randaug-pruned"
    assert TARGETS["character"].collection == "character_ccip_space"
    assert tuple(TARGETS["character"].media_types) == ("Character",)


def test_the_target_table_cannot_be_mutated_by_a_caller():
    """`frozen=True` gèle la référence, pas le contenu d'une liste.

    Un `TARGETS["work"].media_types.append("Character")` quelque part aurait
    corrompu le singleton partagé pour tout le processus, sans une erreur.
    """
    for target in TARGETS.values():
        assert isinstance(target.media_types, tuple)
        with pytest.raises(AttributeError):
            target.media_types.append("Character")  # type: ignore[attr-defined]


def test_a_work_image_is_encoded_by_the_work_model():
    service, engine, _, _ = _service()
    service.encode_image("work", b"png")
    engine.get_image_embedding.assert_called_once_with(
        b"png", model_id="dudcjs2779/anime-style-tag-clip"
    )
    engine.get_character_embedding.assert_not_called()


def test_a_character_image_is_encoded_by_ccip():
    service, engine, _, _ = _service()
    service.encode_image("character", b"png")
    engine.get_character_embedding.assert_called_once_with(b"png")
    engine.get_image_embedding.assert_not_called()


def test_a_work_text_query_uses_the_text_tower_of_the_same_clip_model():
    """Jamais `get_text_embedding` (sentence-transformers) : un autre espace."""
    service, engine, _, _ = _service()
    service.encode_text("work", "une fille aux cheveux blancs")
    engine.get_text_embedding_clip.assert_called_once_with(
        "une fille aux cheveux blancs", model_id=ANIME_CLIP_MODEL_ID
    )
    engine.get_text_embedding.assert_not_called()


def test_a_search_only_ever_touches_its_own_target_collection():
    service, _, _, store = _service()
    service.search("character", [0.3] * 768, limit=5)
    store.search_by_vector.assert_called_once_with(
        "character_ccip_space", [0.3] * 768, limit=5
    )


def test_indexing_writes_under_external_id_and_into_the_target_collection():
    service, _, repo, _ = _service()
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


def test_an_item_whose_image_never_downloaded_is_skipped_not_written():
    """Le téléchargement de la jaquette a échoué : on saute, on n'écrit pas un trou."""
    service, _, repo, _ = _service()
    written = service.index(
        "work",
        [{"external_id": "1", "media_type": "Anime", "title": "Sans image"}],
    )

    assert written == 0
    repo.upsert_items.assert_not_called()


def test_a_dead_image_is_skipped_and_the_rest_of_the_batch_is_still_written():
    """Une image morte ne fait pas tomber le lot — c'est ce que la commande attend.

    Sans ça, une seule jaquette en 404 sur 44 000 ferait échouer l'indexation
    entière.
    """
    service, engine, repo, _ = _service()
    engine.get_image_embedding.side_effect = [
        InferenceError("image illisible"),
        [0.1] * 512,
    ]

    written = service.index(
        "work",
        [
            {
                "external_id": "1",
                "media_type": "Anime",
                "title": "Morte",
                "image_bytes": b"broken",
            },
            {
                "external_id": "2",
                "media_type": "Anime",
                "title": "Vivante",
                "image_bytes": b"png",
            },
        ],
    )

    assert written == 1
    _, ids, vectors, metadatas = repo.upsert_items.call_args[0]
    assert ids == ["2"]
    assert metadatas[0]["title"] == "Vivante"
    assert len(vectors) == 1


def test_an_empty_vector_is_refused_instead_of_being_indexed():
    """Un moteur qui rend `[]` (le repli historique) ne doit pas remplir l'index."""
    service, engine, _, _ = _service()
    engine.get_image_embedding.return_value = []

    with pytest.raises(InferenceError):
        service.encode_image("work", b"png")


def test_text_search_is_refused_on_a_target_with_no_text_tower():
    # CCIP n'a pas d'encodeur de texte. Fusionner un vecteur de phrases générique
    # avec un vecteur CCIP donnerait un nombre qui a l'air juste et ne l'est pas.
    service, _, _, _ = _service()
    with pytest.raises(GameLogicError):
        service.encode_text("character", "une fille aux cheveux blancs")


def test_availability_is_asked_per_target():
    service, _, _, store = _service()
    store.get_collection_count.side_effect = lambda name: (
        12 if name == "unified_clip_space" else 0
    )

    assert service.is_available("work") is True
    assert service.is_available("character") is False


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.encode_image("banana", b"png"),
        lambda s: s.encode_text("banana", "texte"),
        lambda s: s.search("banana", [0.1]),
        lambda s: s.is_available("banana"),
        lambda s: s.index("banana", []),
    ],
    ids=["encode_image", "encode_text", "search", "is_available", "index"],
)
def test_an_unknown_target_is_refused_on_every_entry_point(call):
    service, _, _, _ = _service()
    with pytest.raises(ValueError):
        call(service)


# --------------------------------------------------------------------------
# Le contrat de câblage — contre les VRAIES classes, pas des doublures.
#
# Tous les tests ci-dessus passeraient avec un service câblé sur le mauvais
# provider, ou avec une délégation supprimée du FallbackInferenceAdapter : une
# doublure répond à tout. Ceux-ci résolvent ce que le conteneur injecte VRAIMENT
# et vérifient que chaque méthode appelée existe sur la classe qui la recevra.
# --------------------------------------------------------------------------


def _resolve_provider(provider):
    """Descend la pile d'overrides jusqu'au provider réellement fourni."""
    while getattr(provider, "last_overriding", None) is not None:
        provider = provider.last_overriding
    return provider


def _provided_class(provider):
    """Classe qu'un provider instancierait — sans l'instancier.

    Instancier le FallbackInferenceAdapter ici lancerait de vrais health-checks
    réseau : on veut la CLASSE, pas un objet.
    """
    provides = _resolve_provider(provider).provides
    if isinstance(provides, type):
        return provides
    if isinstance(provides, str):  # "module.path.ClassName"
        module_name, _, class_name = provides.rpartition(".")
        return getattr(importlib.import_module(module_name), class_name)
    # LazyClass(module_name, class_name)
    return getattr(importlib.import_module(provides.module_name), provides.class_name)


def _collaborators():
    from animetix.containers import container

    provider = _resolve_provider(container.core.visual_index_service)
    return {
        name: _provided_class(sub_provider)
        for name, sub_provider in provider.kwargs.items()
    }


def _really_implements(cls, method_name: str, port) -> bool:
    """Vrai seulement si `cls` REDÉFINIT la méthode du port.

    Le port porte des implémentations par défaut qui lèvent
    `InferenceNotImplementedError` : un simple `hasattr` serait vert même si
    quelqu'un supprimait la délégation du FallbackInferenceAdapter.
    """
    own = getattr(cls, method_name, None)
    if own is None:
        return False
    return own is not getattr(port, method_name, None)


def test_the_injected_engine_really_implements_every_method_the_service_calls():
    engine_cls = _collaborators()["inference_engine"]

    for method in (
        "get_image_embedding",
        "get_text_embedding_clip",
        "get_character_embedding",
    ):
        assert _really_implements(engine_cls, method, InferencePort), (
            f"{engine_cls.__name__}.{method} n'est pas implémenté : le service "
            "tomberait sur l'implémentation par défaut du port (qui lève). Sans "
            "cette délégation, trois des quatre opérations de recherche visuelle "
            "sont mortes."
        )


def test_the_injected_repository_can_write_and_the_injected_store_can_search():
    collaborators = _collaborators()

    # L'écriture : seul RepositoryPort porte upsert_items.
    repo_cls = collaborators["repository"]
    assert callable(getattr(repo_cls, "upsert_items", None))

    # La lecture : seul VectorStorePort porte search_by_vector. Câbler la
    # recherche sur `repository` (qui ne l'a pas) était un AttributeError garanti,
    # à chaque appel, pour les deux cibles.
    store_cls = collaborators["vector_store"]
    for method in ("search_by_vector", "get_collection_count"):
        assert callable(getattr(store_cls, method, None)), (
            f"{store_cls.__name__}.{method} n'existe pas : le service est câblé "
            "sur le mauvais provider."
        )
