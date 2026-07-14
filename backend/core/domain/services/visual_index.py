"""Recherche visuelle : une cible, un modèle, une collection.

Le couple (modèle, collection) est indissociable. Deux modèles = deux espaces
vectoriels ; une distance entre deux espaces ne veut rien dire. Ce service est le
seul endroit qui connaît ce couple — partout ailleurs, on demande une cible.

Deux collaborateurs de persistance, et ce n'est pas un oubli : l'ÉCRITURE
(`upsert_items`) n'existe que sur `RepositoryPort`, la RECHERCHE
(`search_by_vector`) n'existe que sur `VectorStorePort`. Aucun des deux ne porte
les deux méthodes. N'en injecter qu'un, c'était appeler une méthode absente —
`AttributeError` à chaque recherche, en production, pour les deux cibles.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from core.utils.model_registry import ANIME_CLIP_MODEL_ID, CCIP_MODEL_ID

from ..exceptions import GameLogicError, InferenceError

logger = logging.getLogger("animetix.visual_index")

# Les deux encodeurs d'image possibles. Le routage se fait sur CE champ, jamais
# en comparant `model_id` à une chaîne d'infrastructure : le jour où un second
# modèle sans tour texte arrive, une comparaison de chaîne l'enverrait
# silencieusement chez CLIP.
ENCODER_CLIP = "clip"
ENCODER_CCIP = "ccip"


def vector_key(media_type: str, external_id: Any) -> str:
    """La clé d'un vecteur dans une collection : « anime:5114 ».

    `MediaItem` n'est unique que sur le COUPLE (external_id, media_type) — un
    external_id nu ne l'est pas. Or la cible `work` verse Anime + Manga + Movie +
    Game dans UNE seule collection, et `VectorRecord` est claveté sur
    (collection_name, item_id) : les ids d'anime viennent de MAL, ceux des films
    de TMDB, ceux des jeux d'IGDB — trois espaces de petits entiers indépendants.
    Écrire sous l'id nu, c'est laisser l'anime n°1 écraser le film n°1, vecteur ET
    métadonnées, sans un mot — et rendre un titre à la place d'un autre.

    UNE seule fonction pour l'écrivain ET le lecteur : le jour où ils construisent
    la clé chacun de leur côté et divergent, la recherche ne rend plus rien et
    rien ne lève.

    Les métadonnées, elles, continuent de porter `external_id` nu et `media_type`
    séparément : ce que l'utilisateur voit ne change pas.

    Pure concaténation des deux champs -- SANS normaliser la casse. Les
    métadonnées rendues au lecteur portent `media_type` tel que `MediaItem`
    l'écrit (`"Anime"`, capitalisé). Un `.lower()` ici forcerait quiconque
    reconstruit la clé à la main (au lieu d'appeler cette fonction) à deviner
    la bonne casse ; se tromper ne lève rien -- la recherche par id ne rend
    juste plus rien.
    """
    return f"{media_type}:{external_id}"


@dataclass(frozen=True)
class Target:
    name: str
    model_id: str
    collection: str
    # Un tuple, pas une liste : `TARGETS["work"].media_types.append("Character")`
    # corromprait le singleton partagé pour tout le processus, sans un mot —
    # `frozen=True` gèle la référence, pas le contenu.
    media_types: Tuple[str, ...]
    image_encoder: str
    has_text_tower: bool


TARGETS: Dict[str, Target] = {
    "work": Target(
        name="work",
        # CLIP EVA-02 affiné sur de l'illustration japonaise : une jaquette est un
        # dessin, pas une photo.
        model_id=ANIME_CLIP_MODEL_ID,
        collection="unified_clip_space",
        media_types=("Anime", "Manga", "Movie", "Game"),
        image_encoder=ENCODER_CLIP,
        has_text_tower=True,  # CLIP est un espace joint : la recherche texte est gratuite
    ),
    "character": Target(
        name="character",
        # CCIP répond à « est-ce le MÊME personnage ? ». Pas d'encodeur de texte.
        model_id=CCIP_MODEL_ID,
        collection="character_ccip_space",
        media_types=("Character",),
        image_encoder=ENCODER_CCIP,
        has_text_tower=False,
    ),
}


class VisualIndexService:
    def __init__(self, inference_engine, repository, vector_store):
        self.inference_engine = inference_engine
        self.repository = repository  # écriture : upsert_items
        self.vector_store = vector_store  # lecture : search_by_vector / count

    def target(self, name: str) -> Target:
        if name not in TARGETS:
            raise ValueError(f"Cible de recherche visuelle inconnue : {name!r}")
        return TARGETS[name]

    @staticmethod
    def _checked(vector: List[float], what: str) -> List[float]:
        """Un vecteur vide n'est pas un résultat : c'est une panne déguisée."""
        if not vector:
            raise InferenceError(
                f"{what} a rendu un vecteur vide — refus de l'indexer ou de "
                "chercher avec : il classerait arbitrairement."
            )
        return vector

    def encode_image(self, target: str, image_data: bytes) -> List[float]:
        spec = self.target(target)
        if spec.image_encoder == ENCODER_CCIP:
            vector = self.inference_engine.get_character_embedding(image_data)
        elif spec.image_encoder == ENCODER_CLIP:
            vector = self.inference_engine.get_image_embedding(
                image_data, model_id=spec.model_id
            )
        else:  # une cible mal déclarée ne doit pas router au hasard
            raise ValueError(
                f"Encodeur d'image inconnu pour la cible {spec.name!r} : "
                f"{spec.image_encoder!r}"
            )
        return self._checked(vector, f"{spec.image_encoder} ({spec.model_id})")

    def encode_text(self, target: str, text: str) -> List[float]:
        spec = self.target(target)
        if not spec.has_text_tower:
            raise GameLogicError(
                f"La cible « {spec.name} » n'a pas d'encodeur de texte : "
                "recherche par description impossible."
            )
        # La tour texte du MÊME modèle. Jamais un encodeur de phrases générique :
        # la recherche fait la moyenne du texte et de l'image, et une moyenne
        # entre deux espaces est soit une erreur, soit un mensonge plausible.
        vector = self.inference_engine.get_text_embedding_clip(
            text, model_id=spec.model_id
        )
        return self._checked(vector, f"la tour texte de {spec.model_id}")

    def search(self, target: str, vector: List[float], limit: int = 10) -> List[Dict]:
        spec = self.target(target)
        return self.vector_store.search_by_vector(spec.collection, vector, limit=limit)

    def is_available(self, target: str) -> bool:
        spec = self.target(target)
        return self.vector_store.get_collection_count(spec.collection) > 0

    def index(self, target: str, items: List[Dict[str, Any]]) -> int:
        """Encode et écrit un lot. Une image morte est sautée, jamais fatale."""
        spec = self.target(target)
        ids, vectors, metadatas = [], [], []
        for item in items:
            image_bytes = item.get("image_bytes")
            if not image_bytes:
                continue
            try:
                vector = self.encode_image(target, image_bytes)
            except Exception as e:  # une image morte ne fait pas tomber le lot
                logger.warning("Image illisible pour %s : %s", item.get("title"), e)
                continue
            ids.append(vector_key(item["media_type"], item["external_id"]))
            vectors.append(vector)
            # Ce qu'on écrit ICI est ce que l'utilisateur verra : le lecteur rend
            # ces métadonnées telles quelles au sérialiseur.
            metadatas.append(
                {
                    "external_id": str(item["external_id"]),
                    "media_type": item["media_type"],
                    "title": item.get("title"),
                    "image": item.get("image"),
                }
            )
        if not ids:
            return 0
        # `strict=True` : par défaut, `upsert_items` journalise l'échec et rend la
        # main. Le compte rendu ici serait alors `len(ids)` — le nombre de vecteurs
        # qu'on AURAIT écrits. Un décalage de dimension ou un verrou expiré annule
        # tout le lot (l'upsert tourne dans un `transaction.atomic()`) et on
        # annoncerait quand même le succès : exactement la panne silencieuse que ce
        # module existe pour empêcher. Le nombre rendu doit être le nombre de
        # vecteurs réellement dans la collection, ou rien.
        self.repository.upsert_items(
            spec.collection, ids, vectors, metadatas, strict=True
        )
        return len(ids)
