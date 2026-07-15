import hashlib
import random
from typing import Dict, List, Optional, Tuple

from ...ports.repository_port import RepositoryPort

# Locales jouables, dans l'ordre où elles sont proposées quand aucune n'est imposée.
PLAYABLE_LOCALES = ("ja", "fr")


class CoverTestDomainService:
    def __init__(self, repository: RepositoryPort):
        self.repository = repository
        self._metadata = None
        self._candidates: Dict[Tuple[str, ...], List[str]] = {}

    def _get_metadata(self):
        if self._metadata is None:
            self._metadata = self.repository.get_manga_covers_metadata()
            self._candidates.clear()
        return self._metadata

    def _variants(self, data: Dict, locales: Tuple[str, ...]) -> List[Tuple[str, Dict]]:
        """(locale, cover) de chaque volume disponible dans les locales demandées."""
        cover_map = data.get("covers") or {}
        return [
            (loc, variant)
            for loc in locales
            for variant in (cover_map.get(loc) or [])
            if variant.get("url")
        ]

    def _eligible_manga_ids(self, locales: Tuple[str, ...]) -> List[str]:
        """Mangas ayant au moins une cover dans ces locales. Mémoïsé, trié (déterminisme
        du tirage quotidien)."""
        if locales not in self._candidates:
            metadata = self._get_metadata() or []
            eligible = []
            for item in metadata:
                has_loc = False
                for loc in locales:
                    if loc == "ja" and item.get("has_ja"):
                        has_loc = True
                    elif loc == "fr" and item.get("has_fr"):
                        has_loc = True
                if has_loc:
                    eligible.append(item["id"])
            self._candidates[locales] = sorted(eligible)
        return self._candidates[locales]

    def get_random_cover(self, locale: Optional[str] = None) -> Optional[Dict]:
        return self._pick_cover(locale)

    def list_titles(self) -> list:
        """Titles of every manga that has at least one cover (the only valid answers)."""
        metadata = self._get_metadata() or []
        return sorted({item["title"] for item in metadata if item.get("title")})

    def list_entries(self) -> list:
        """(id, title, aliases) for every manga that has a cover. Aliases (English /
        native / synonyms, sourced from AniList in the data file) let players search a
        manga by its Japanese romaji OR its English name."""
        metadata = self._get_metadata() or []
        out = []
        for item in metadata:
            if not item.get("title"):
                continue
            aliases = []
            for field in ("title_english", "title_native"):
                if item.get(field):
                    aliases.append(item[field])
            aliases += item.get("synonyms", []) or []
            out.append(
                {"id": str(item["id"]), "title": item["title"], "aliases": aliases}
            )
        out.sort(key=lambda e: e["title"].lower())
        return out

    def image_for_title(
        self, title: str, locale: Optional[str] = None
    ) -> Optional[str]:
        """A representative cover URL (volume 1 if possible) for a given manga title."""
        info = self.repository.get_manga_cover_by_title(title)
        if not info:
            return None
        cover_map = info.get("covers", {})
        locales = [locale] if locale else list(cover_map.keys())
        for loc in locales:
            variants = cover_map.get(loc) or []
            if variants:
                pick = next(
                    (v for v in variants if v.get("volume") == "1"), variants[0]
                )
                return pick.get("url")
        return None

    def get_daily_cover(self, date_obj) -> Optional[Dict]:
        seed = int(
            hashlib.md5(
                f"covertest-{date_obj}".encode(), usedforsecurity=False
            ).hexdigest(),
            16,
        )
        return self._pick_cover(seed=seed)

    def _pick_cover(
        self, locale: Optional[str] = None, seed: Optional[int] = None
    ) -> Optional[Dict]:
        """Tire une cover parmi **tous** les volumes disponibles.

        Le manga est tiré uniformément (une série de 60 tomes ne doit pas sortir
        60 fois plus souvent qu'un one-shot), puis le volume uniformément parmi
        les siens. `seed` utilise un RNG local : le tirage quotidien reste
        déterministe sans muter le RNG global partagé entre les threads ASGI.
        """
        rng = random.Random(seed) if seed is not None else random
        locales = (locale,) if locale else PLAYABLE_LOCALES

        manga_ids = self._eligible_manga_ids(locales)
        if not manga_ids:
            return None

        manga_id = rng.choice(manga_ids)
        data = self.repository.get_manga_cover_by_id(manga_id)
        if not data:
            return None
        loc, cover = rng.choice(self._variants(data, locales))

        return {
            "manga_id": manga_id,
            "manga_title": data["title"],
            "cover_url": cover["url"],
            "locale": loc,
            "volume": cover.get("volume"),
            "author": data.get("author"),
        }
