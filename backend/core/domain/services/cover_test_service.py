import hashlib
import random
from typing import Dict, List, Optional, Tuple

from ...ports.repository_port import RepositoryPort

# Locales jouables, dans l'ordre où elles sont proposées quand aucune n'est imposée.
PLAYABLE_LOCALES = ("ja", "fr")


class CoverTestDomainService:
    def __init__(self, repository: RepositoryPort):
        self.repository = repository
        self._covers = None
        self._candidates: Dict[Tuple[str, ...], List[str]] = {}

    def _get_covers(self):
        if self._covers is None:
            self._covers = self.repository.load_covers()
            self._candidates.clear()  # l'index dérive des covers : il se recalcule avec
        return self._covers

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
            covers = self._get_covers() or {}
            self._candidates[locales] = sorted(
                mid for mid, data in covers.items() if self._variants(data, locales)
            )
        return self._candidates[locales]

    def get_random_cover(self, locale: Optional[str] = None) -> Optional[Dict]:
        return self._pick_cover(locale)

    def list_titles(self) -> list:
        """Titles of every manga that has at least one cover (the only valid answers)."""
        covers = self._get_covers() or {}
        return sorted({info["title"] for info in covers.values() if info.get("title")})

    def list_entries(self) -> list:
        """(id, title, aliases) for every manga that has a cover. Aliases (English /
        native / synonyms, sourced from AniList in the data file) let players search a
        manga by its Japanese romaji OR its English name."""
        covers = self._get_covers() or {}
        out = []
        for mid, info in covers.items():
            if not info.get("title"):
                continue
            aliases = []
            for field in ("title_english", "title_native"):
                if info.get(field):
                    aliases.append(info[field])
            aliases += info.get("synonyms", []) or []
            out.append({"id": str(mid), "title": info["title"], "aliases": aliases})
        out.sort(key=lambda e: e["title"].lower())
        return out

    def image_for_title(
        self, title: str, locale: Optional[str] = None
    ) -> Optional[str]:
        """A representative cover URL (volume 1 if possible) for a given manga title."""
        covers = self._get_covers() or {}
        for info in covers.values():
            if info.get("title") != title:
                continue
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
        covers_data = self._get_covers()
        if not covers_data:
            return None

        rng = random.Random(seed) if seed is not None else random
        locales = (locale,) if locale else PLAYABLE_LOCALES

        manga_ids = self._eligible_manga_ids(locales)
        if not manga_ids:
            return None

        manga_id = rng.choice(manga_ids)
        data = covers_data[manga_id]
        loc, cover = rng.choice(self._variants(data, locales))

        return {
            "manga_id": manga_id,
            "manga_title": data["title"],
            "cover_url": cover["url"],
            "locale": loc,
            "volume": cover.get("volume"),
            "author": data.get("author"),
        }
