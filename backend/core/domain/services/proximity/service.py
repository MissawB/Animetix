"""Classe le catalogue face à un secret, et dit au joueur ce qui l'a rapproché."""

import logging
from typing import Any, Dict, List, Optional

from ...exceptions import GameLogicError
from .components import (
    W_CO_RECO,
    W_DIRECT,
    W_TAGS,
    Components,
    ProximityIndex,
    build_index,
    score,
)

logger = logging.getLogger("animetix.proximity")

# Les seuils du bridage. Sous WARM, une proposition n'apprend RIEN : une proposition
# froide qui renseignerait rendrait l'élimination aussi rentable que la recherche.
WARM = 50.0  # une seule composante, la dominante
HOT = 80.0  # les deux plus fortes, avec leur contenu


class ProximityService:
    def __init__(self, catalog_service):
        self.catalog_service = catalog_service
        self._indexes: Dict[str, ProximityIndex] = {}

    def _index(self, media_type: str) -> ProximityIndex:
        if media_type not in self._indexes:
            catalog = self.catalog_service.load_data(media_type) or {}
            works = catalog.get("db") or []
            index = build_index(works)
            if not index.works:
                raise GameLogicError(
                    f"Proximité impossible : le catalogue {media_type} est vide."
                )
            self._indexes[media_type] = index
        return self._indexes[media_type]

    def rank(self, media_type: str, secret_title: str) -> List[str]:
        """Tout le catalogue, le plus proche du secret en tête. Le secret est exclu."""
        index = self._index(media_type)
        scored = [
            (score(index, secret_title, title).total(), title)
            for title in index.works
            if title != secret_title
        ]
        if not any(value > 0 for value, _ in scored):
            # Aucun signal exploitable : ni recommandation, ni tag partagé. On le DIT.
            # Rendre un classement arbitraire (ou des 0.0 qui ont l'air de vrais chiffres)
            # est exactement le piège dans lequel ce jeu est tombé.
            raise GameLogicError(
                f"Proximité impossible : aucun signal pour {media_type} / {secret_title}."
            )
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [title for _, title in scored]

    def report(
        self,
        media_type: str,
        secret_title: str,
        guess_title: str,
        ranking: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Le rang d'une proposition, et — au-dessus des seuils — ce qui l'a rapprochée."""
        ranking = (
            ranking if ranking is not None else self.rank(media_type, secret_title)
        )
        total = len(ranking)
        if guess_title not in ranking:
            # Le secret lui-même, ou un titre hors catalogue : le jeu tranche ailleurs.
            return {"percent": 100.0, "rank": 0, "total": total, "reasons": []}

        position = ranking.index(guess_title)  # 0 = rien n'est plus proche
        rank = position + 1
        # Percentile, pas un ratio sur (total - 1) : « 30e sur 2181 » doit lire 98,6 %
        # (2151/2181, la part du catalogue qu'on dépasse), pas 98,7 % (2151/2180). Sur
        # ce fixture, la variante (total - 1) produit une égalité exacte à 80,0 pour
        # Psycho-Pass et le fait basculer côté HOT alors qu'il doit rester WARM.
        percent = round(100.0 * (total - rank) / total, 1)

        index = self._index(media_type)
        components = score(index, secret_title, guess_title)
        return {
            "percent": percent,
            "rank": rank,
            "total": total,
            "reasons": self._reasons(
                index, secret_title, guess_title, components, percent
            ),
        }

    def _reasons(
        self,
        index: ProximityIndex,
        secret: str,
        guess: str,
        components: Components,
        percent: float,
    ) -> List[Dict[str, Any]]:
        if percent < WARM:
            return []  # une proposition froide n'apprend rien

        shared_tags = sorted(
            set(index.works[secret].get("tags") or [])
            & set(index.works[guess].get("tags") or []),
            key=lambda t: -index.idf.get(t, 0.0),
        )
        candidates = [
            {
                "kind": "public",
                "weight": W_DIRECT * components.direct + W_CO_RECO * components.co_reco,
                "label": "C'est le public qui vous rapproche",
                "detail": [],
            },
            {
                "kind": "tags",
                "weight": W_TAGS * components.tags,
                "label": f"{len(shared_tags)} tag(s) partagé(s)",
                "detail": shared_tags[:3],
            },
            {
                "kind": "structure",
                "weight": components.bonus,
                "label": "Même famille (studio, source ou époque)",
                "detail": [],
            },
        ]
        ranked = sorted(
            (c for c in candidates if c["weight"] > 0), key=lambda c: -c["weight"]
        )
        # Le bonus structurel n'est JAMAIS montré seul : sinon la première proposition
        # tiède donnerait le studio du secret, et le catalogue fondrait d'un coup. Il ne
        # peut apparaître qu'en SECOND, derrière une vraie composante.
        substantive = [c for c in ranked if c["kind"] != "structure"]
        if not substantive:
            return []
        if percent < HOT:
            chosen = substantive[:1]
        else:
            chosen = (substantive + [c for c in ranked if c["kind"] == "structure"])[:2]

        for reason in chosen:
            reason.pop("weight")
            if percent < HOT:
                reason["detail"] = []  # le contenu n'apparaît qu'à partir de HOT
        return chosen
