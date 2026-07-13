"""Classe le catalogue face à un secret, et dit au joueur ce qui l'a rapproché."""

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ...exceptions import GameLogicError
from .components import (
    W_CO_RECO,
    W_DIRECT,
    W_TAGS,
    Components,
    ProximityIndex,
    build_index,
    score,
    vocabulary_of,
)

logger = logging.getLogger("animetix.proximity")

# Les seuils du bridage. Sous WARM, une proposition n'apprend RIEN : une proposition
# froide qui renseignerait rendrait l'élimination aussi rentable que la recherche.
WARM = 50.0  # une seule composante, la dominante
HOT = 80.0  # les deux plus fortes, avec leur contenu

# Le percentile SEUL ne suffit pas à brider : dans un catalogue à longue traîne, être
# au 80e percentile ne veut pas dire « proche ». Mesuré sur le vrai catalogue Anime
# (2181 œuvres, secret = DEATH NOTE) : le 80e percentile tombe sur un score BRUT de
# 0,058 (Re:Zero), et 436 œuvres -- 20 % du catalogue -- franchissaient HOT et se
# voyaient offrir trois des tags du secret. Une romcom qui ne partage que « Primarily
# Male Cast » ne doit pas reconstruire la liste de tags du secret.
#
# Une raison ne peut donc sortir que si le score BRUT (Components.total()) franchit
# aussi un plancher, quel que soit le rang.
#
# WARM_FLOOR = 0.05 : le bruit de fond du vocabulaire. Un seul tag banal partagé vaut
# ~0,02-0,035 sur le vrai catalogue (DEATH NOTE ~ Kimetsu no Yaiba = 0,035, deux
# œuvres SANS rapport). 0,05 est juste au-dessus de cette bande : nommer une
# composante (sans son contenu) exige mieux qu'une coïncidence de vocabulaire.
#
# HOT_FLOOR = 0.20 : livrer le CONTENU (les tags partagés) exige un vrai lien.
# 0,20 est mesuré, et choisi sous W_TAGS (0,25) à dessein : un catalogue qui n'a QUE
# du vocabulaire -- les jeux vidéo (0 tag, 100 % genres), les personnages (traits et
# organisations, aucune recommandation) -- doit pouvoir atteindre HOT, sinon ces
# modes n'expliquent jamais rien. Au-dessus de 0,20, il faut soit un recouvrement de
# vocabulaire quasi total, soit le graphe de recommandations. Sur le vrai catalogue,
# face à DEATH NOTE : 40 œuvres sur 2180 (1,8 %) franchissent 0,20, contre 436 (20 %)
# avec le seul percentile.
WARM_FLOOR = 0.05
HOT_FLOOR = 0.20

# Un classement : (titre, score brut), du plus proche au plus lointain. Le score fait
# partie du classement -- sans lui, report() ne peut compter que des positions d'index,
# et le percentile d'une proposition sans le moindre signal devient une fonction de la
# place de son nom dans l'alphabet.
Ranking = List[Tuple[str, float]]


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

    def rank(self, media_type: str, secret_title: str) -> Ranking:
        """Tout le catalogue avec son score, le plus proche du secret en tête.

        Le secret est exclu. Les ex æquo se suivent (ordre alphabétique pour
        l'affichage), mais cet ordre n'a AUCUN effet sur le percentile : celui-ci
        se calcule sur les scores (cf. report), jamais sur la position.
        """
        index = self._index(media_type)
        scored = [
            (title, score(index, secret_title, title).total())
            for title in index.works
            if title != secret_title
        ]
        if not any(value > 0 for _, value in scored):
            # Aucun signal exploitable : ni recommandation, ni tag partagé. On le DIT.
            # Rendre un classement arbitraire (ou des 0.0 qui ont l'air de vrais chiffres)
            # est exactement le piège dans lequel ce jeu est tombé.
            raise GameLogicError(
                f"Proximité impossible : aucun signal pour {media_type} / {secret_title}."
            )
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored

    def _as_ranking(
        self, media_type: str, secret_title: str, ranking: Optional[Sequence]
    ) -> Ranking:
        """Accepte un classement (titre, score) -- ou une simple liste de titres.

        Une liste de titres nue est ce qu'une version antérieure mettait en cache :
        elle ne porte plus l'information nécessaire au percentile. Plutôt que de
        deviner (c'était le bug), on recalcule.
        """
        if not ranking:
            return self.rank(media_type, secret_title)
        if isinstance(ranking[0], (list, tuple)):
            return [(title, float(value)) for title, value in ranking]
        logger.debug(
            "Classement sans scores (cache d'une version antérieure) : recalcul."
        )
        return self.rank(media_type, secret_title)

    def report(
        self,
        media_type: str,
        secret_title: str,
        guess_title: str,
        ranking: Optional[Sequence] = None,
    ) -> Dict[str, Any]:
        """Le rang d'une proposition, et — au-dessus des seuils — ce qui l'a rapprochée."""
        scored = self._as_ranking(media_type, secret_title, ranking)
        total = len(scored)

        if guess_title == secret_title:
            # Le secret lui-même : il n'est pas dans le classement, mais rien n'est
            # plus proche de lui que lui. Le jeu tranche ailleurs (check_title_match)
            # et remplace ce score par 100 ; on ne doit surtout pas le confondre avec
            # un titre inconnu et le renvoyer à 0.
            return {"percent": 100.0, "rank": 0, "total": total, "reasons": []}

        values = [value for _, value in scored]
        guess_score = next(
            (value for title, value in scored if title == guess_title), None
        )
        if guess_score is None:
            # Un titre hors catalogue. report() est l'unique couture de scoring de DEUX
            # jeux : rendre le score MAXIMAL pour « je ne connais pas ce titre » est le
            # défaut le plus dangereux possible (le duel, qui ne validait pas la
            # proposition, diffusait « 100 % » à toute la salle pour n'importe quelle
            # trame). On rend le score le plus FROID, sans aucune raison : une
            # proposition qu'on ne sait pas situer n'apprend rien et ne vaut rien.
            # Pas une exception : ce chemin est appelé depuis une boucle websocket
            # vivante, où un GameLogicError se lirait « scoring indisponible » -- un
            # mensonge sur la cause. La validation, elle, appartient aux appelants
            # (classique et duel la font tous les deux) ; ceci est le filet.
            logger.warning(
                "Proximité : titre hors catalogue %r (%s / secret %r) -> 0 %%.",
                guess_title,
                media_type,
                secret_title,
            )
            return {"percent": 0.0, "rank": total, "total": total, "reasons": []}

        # Le percentile se calcule sur la part du catalogue STRICTEMENT dépassée, pas
        # sur une position d'index : sinon les ex æquo se départagent par leur nom.
        # Sur le vrai catalogue personnages, 32 280 des 32 384 noms scorent EXACTEMENT
        # 0 face à Levi : classés par (-score, titre), ils occupaient les rangs 105 à
        # 32 384 et un parfait inconnu lisait « 99,7 %, Brûlant » parce que son nom
        # commence par une lettre précoce. Les ex æquo partagent désormais leur rang,
        # et « les œuvres à score nul sortent toutes glacial, ce qui est la vérité ».
        strictly_below = sum(1 for value in values if value < guess_score)
        strictly_above = sum(1 for value in values if value > guess_score)
        rank = strictly_above + 1  # 1 = rien n'est plus proche

        percent = round(100.0 * strictly_below / (total - 1), 1) if total > 1 else 100.0
        # 100 % veut dire « rien n'est plus proche » -- l'invariant de la spec. Sur
        # 32 384 personnages, le 15e meilleur score dépasse 99,96 % du catalogue et
        # arrondirait à 100,0 : on le retient sous la barre.
        if strictly_above and percent >= 100.0:
            percent = 99.9

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
        raw = components.total()
        # Le bridage tient sur DEUX choses : le rang (le joueur doit être devant le
        # gros du catalogue) ET le score brut (le rang seul ne veut pas dire
        # « proche » dans un catalogue à longue traîne -- cf. WARM_FLOOR/HOT_FLOOR).
        if percent < WARM or raw < WARM_FLOOR:
            return []  # une proposition froide n'apprend rien

        # Le même vocabulaire fusionné que la composante qui score dessus (cf.
        # vocabulary_of dans components.py) : tags, genres, traits, organisations.
        # Un genre n'est qu'un tag très fréquent, et c'est tout ce que le mode Game
        # partage (0 tag, 100 % genres) ; un personnage, lui, ne porte ni l'un ni
        # l'autre, seulement traits/organisations. Relire uniquement "tags" ici
        # ferait mentir le service : un score "tags" non nul porté entièrement par
        # des genres ou des organisations partagés s'afficherait avec un detail vide.
        shared_vocabulary = sorted(
            vocabulary_of(index.works[secret]) & vocabulary_of(index.works[guess]),
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
                "label": f"{len(shared_vocabulary)} point(s) commun(s) (tags/genres) partagé(s)",
                "detail": shared_vocabulary[:3],
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

        hot = percent >= HOT and raw >= HOT_FLOOR
        if not hot:
            chosen = substantive[:1]
        else:
            chosen = (substantive + [c for c in ranked if c["kind"] == "structure"])[:2]

        for reason in chosen:
            reason.pop("weight")
            if not hot:
                reason["detail"] = []  # le contenu n'apparaît qu'à partir de HOT
        return chosen
