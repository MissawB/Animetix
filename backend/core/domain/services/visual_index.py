"""Recherche visuelle : une cible, un modèle, une collection.

Le couple (modèle, collection) est indissociable. Deux modèles = deux espaces
vectoriels ; une distance entre deux espaces ne veut rien dire. Ce service est le
seul endroit qui connaît ce couple — partout ailleurs, on demande une cible.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from adapters.inference.ccip_vision import CCIP_MODEL_ID

from ..exceptions import GameLogicError

logger = logging.getLogger("animetix.visual_index")


@dataclass(frozen=True)
class Target:
    name: str
    model_id: str
    collection: str
    media_types: List[str]
    has_text_tower: bool


TARGETS: Dict[str, Target] = {
    "work": Target(
        name="work",
        # CLIP EVA-02 affiné sur de l'illustration japonaise : une jaquette est un
        # dessin, pas une photo.
        model_id="dudcjs2779/anime-style-tag-clip",
        collection="unified_clip_space",
        media_types=["Anime", "Manga", "Movie", "Game"],
        has_text_tower=True,  # CLIP est un espace joint : la recherche texte est gratuite
    ),
    "character": Target(
        name="character",
        # CCIP répond à « est-ce le MÊME personnage ? ». Pas d'encodeur de texte.
        # `CCIP_MODEL_ID` est importé de l'adaptateur qui charge réellement le
        # graphe ONNX -- jamais recopié ici : `deepghs/ccip` (le dépôt de base,
        # checkpoints torch) ne sert aucun graphe, seul `deepghs/ccip_onnx/...`
        # est chargé en pratique.
        model_id=CCIP_MODEL_ID,
        collection="character_ccip_space",
        media_types=["Character"],
        has_text_tower=False,
    ),
}


class VisualIndexService:
    def __init__(self, inference_engine, repository):
        self.inference_engine = inference_engine
        self.repository = repository

    def target(self, name: str) -> Target:
        if name not in TARGETS:
            raise ValueError(f"Cible de recherche visuelle inconnue : {name!r}")
        return TARGETS[name]

    def encode_image(self, target: str, image_data: bytes) -> List[float]:
        spec = self.target(target)
        if spec.model_id == CCIP_MODEL_ID:
            return self.inference_engine.get_character_embedding(image_data)
        return self.inference_engine.get_image_embedding(
            image_data, model_id=spec.model_id
        )

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
        return self.inference_engine.get_text_embedding_clip(
            text, model_id=spec.model_id
        )

    def search(self, target: str, vector: List[float], limit: int = 10) -> List[Dict]:
        spec = self.target(target)
        return self.repository.search_by_vector(spec.collection, vector, limit=limit)

    def is_available(self, target: str) -> bool:
        spec = self.target(target)
        return self.repository.get_collection_count(spec.collection) > 0

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
            ids.append(str(item["external_id"]))
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
        self.repository.upsert_items(spec.collection, ids, vectors, metadatas)
        return len(ids)
