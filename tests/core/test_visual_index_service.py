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
from core.domain.services.visual_index import TARGETS, VisualIndexService, vector_key
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


def test_search_rewrites_id_to_the_bare_external_id_the_reader_can_resolve():
    """CRITICAL: `PgVectorStoreAdapter.search_by_vector` sets `doc["id"]` to
    the composite key the writer used (`vector_key`, e.g. "Anime:5114").
    `MediaItemSerializer` has no `external_id` field, only `id` -- so without
    this rewrite the composite key travels to the frontend unchanged,
    `SearchBar.tsx` navigates to `/media/Anime/Anime:5114/`, and
    `MediaDetailView` looks up `external_id="Anime:5114"` (a value that was
    never written): 404 on every single visual-search result, silently.
    """
    service, _, _, store = _service()
    store.search_by_vector.return_value = [
        {
            "id": "Anime:5114",
            "external_id": "5114",
            "media_type": "Anime",
            "title": "Fullmetal Alchemist",
        }
    ]

    results = service.search("work", [0.1] * 512, limit=1)

    assert results[0]["id"] == "5114"
    # The composite key is not lost -- callers that still need it have
    # `external_id` + `media_type` to rebuild it via `vector_key`.
    assert results[0]["external_id"] == "5114"
    assert results[0]["media_type"] == "Anime"


def test_search_leaves_id_alone_when_metadata_carries_no_external_id():
    """A defensive default: if a caller's fake vector store doesn't stamp
    `external_id` (e.g. a minimal test double), the rewrite must not crash or
    blank out `id` -- it leaves it exactly as the store returned it."""
    service, _, _, store = _service()
    store.search_by_vector.return_value = [{"id": "7", "title": "NoExternalId"}]

    results = service.search("work", [0.1] * 512, limit=1)

    assert results[0]["id"] == "7"


def test_indexing_writes_under_the_composite_key_and_into_the_target_collection():
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
    # `media_type:external_id` : l'external_id nu n'est unique que PAR type, et
    # quatre types partagent cette collection. Pure concaténation -- la casse
    # de `media_type` n'est PAS normalisée (`MediaItem` l'écrit "Anime").
    assert ids == ["Anime:38000"]
    assert ids == [vector_key("Anime", "38000")]
    # Les métadonnées, elles, ne changent pas : c'est ce que l'utilisateur voit.
    assert metadatas[0]["external_id"] == "38000"
    assert metadatas[0]["media_type"] == "Anime"
    assert metadatas[0]["title"] == "Kimetsu"


def test_two_media_types_sharing_a_bare_id_do_not_collide():
    """L'anime n°1 (MAL) et le film n°1 (TMDB) vont dans la MÊME collection.

    Sous l'id nu, le second écrasait le premier — vecteur et métadonnées — et on
    servait un titre à la place d'un autre, sans une erreur.
    """
    service, _, repo, _ = _service()
    service.index(
        "work",
        [
            {
                "external_id": "1",
                "media_type": "Anime",
                "title": "Cowboy Bebop",
                "image_bytes": b"png",
            },
            {
                "external_id": "1",
                "media_type": "Movie",
                "title": "Toy Story",
                "image_bytes": b"png",
            },
        ],
    )

    _, ids, _, _ = repo.upsert_items.call_args[0]
    assert ids == ["Anime:1", "Movie:1"]
    assert len(set(ids)) == 2


def test_vector_key_does_not_lowercase_media_type():
    """La clé est une concaténation PURE des deux champs -- pas de casse
    normalisée. Les métadonnées rendues au lecteur portent `media_type` tel
    que `MediaItem` l'écrit (`"Anime"`, capitalisé, via ses `choices`) : un
    lecteur qui reconstruit la clé à la main avec
    `f"{item['media_type']}:{item['external_id']}"` doit retomber sur
    EXACTEMENT ce que `vector_key` aurait produit -- sinon la recherche par id
    ne rend plus rien, silencieusement, un f-string après l'autre.
    """
    assert vector_key("Anime", "38000") == "Anime:38000"
    assert vector_key("Anime", "38000") != "anime:38000"


def test_the_id_the_writer_wrote_is_the_id_the_reader_looks_up():
    """Bout en bout : ce que `index()` écrit sous cette clé doit être
    exactement ce qu'un lecteur retrouve en rebâtissant la clé depuis les
    métadonnées qu'il vient de lire (`media_type` + `external_id`, tels que
    remis au sérialiseur) -- pas un id devine a la main."""
    service, _, repo, _ = _service()
    service.index(
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

    _, ids, _, metadatas = repo.upsert_items.call_args[0]
    written_id = ids[0]
    metadata = metadatas[0]

    # Le lecteur ne connait que les métadonnées (ce que le sérialiseur rend à
    # l'utilisateur) -- il doit pouvoir retrouver le MÊME id en appelant la
    # MÊME fonction que l'écrivain, jamais en le reconstruisant à la main.
    assert vector_key(metadata["media_type"], metadata["external_id"]) == written_id


def test_a_failed_write_is_not_counted_as_written():
    """Le dépôt journalise et rend la main par défaut : le service DOIT écrire en
    mode strict, sans quoi il rend `len(ids)` — le nombre de vecteurs qu'il aurait
    écrits — et la commande annonce en vert un lot annulé."""
    service, _, repo, _ = _service()
    repo.upsert_items.side_effect = RuntimeError("dimension mismatch")

    with pytest.raises(RuntimeError):
        service.index(
            "work",
            [{"external_id": "1", "media_type": "Anime", "image_bytes": b"png"}],
        )

    assert repo.upsert_items.call_args.kwargs["strict"] is True


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
    assert ids == ["Anime:2"]
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


def test_the_production_chain_can_actually_serve_visual_search():
    """Le test précédent vérifie une CLASSE (`FallbackInferenceAdapter`) qui
    délègue TOUJOURS aux trois méthodes -- que la délégation trouve preneur ou
    non. Il resterait vert même si aucun moteur de la chaîne production ne
    servait plus rien : c'est exactement le trou que ce module documente
    (`build_inference_chain` rend `[brain_api, google_genai]` quand
    `LOCAL_INFERENCE_ENABLED` est faux -- le cas du conteneur web en prod).

    Celui-ci descend d'un niveau : il prend la forme RÉELLE de la chaîne
    production et vérifie qu'au moins un de ses membres implémente VRAIMENT
    chacune des trois méthodes. Avant que `BrainAPIAdapter` ne les porte, ce
    test échouait pour `get_text_embedding_clip` et `get_character_embedding` :
    ni `BrainAPIAdapter` ni `GoogleGenAIAdapter` ne les servait, et
    `FallbackInferenceAdapter._fallback_call` n'avait personne à qui déléguer --
    une `InferenceError` à chaque recherche visuelle, en production, silencieuse
    jusqu'au premier utilisateur qui l'aurait rencontrée.
    """
    from adapters.inference.brain_api_adapter import BrainAPIAdapter
    from adapters.inference.google_genai_adapter import GoogleGenAIAdapter
    from animetix.containers.inference import build_inference_chain

    # La forme réelle de la chaîne production (`local_enabled=False`) : deux
    # jetons de classe suffisent, `build_inference_chain` ne fait que les ordonner.
    prod_chain = build_inference_chain(
        local_enabled=False,
        unified="unified",
        compact_reasoning="compact_reasoning",
        local_text="local_text",
        brain_api="brain_api",
        google_genai="google_genai",
        local_guardrail="local_guardrail",
    )
    assert prod_chain == ["brain_api", "google_genai"]

    chain_classes = [BrainAPIAdapter, GoogleGenAIAdapter]
    for method in (
        "get_image_embedding",
        "get_text_embedding_clip",
        "get_character_embedding",
    ):
        assert any(
            _really_implements(cls, method, InferencePort) for cls in chain_classes
        ), (
            f"Aucun membre de la chaîne production "
            f"({[c.__name__ for c in chain_classes]}) n'implémente {method} : "
            "en production, FallbackInferenceAdapter ne trouve personne à qui "
            "déléguer et chaque recherche visuelle échoue."
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
