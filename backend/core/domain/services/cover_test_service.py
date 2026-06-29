import hashlib
import random
from typing import Dict, Optional

from ...ports.repository_port import RepositoryPort


class CoverTestDomainService:
    def __init__(self, repository: RepositoryPort):
        self.repository = repository
        self._covers = None

    def _get_covers(self):
        if self._covers is None:
            self._covers = self.repository.load_covers()
        return self._covers

    def get_random_cover(self, locale: Optional[str] = None) -> Optional[Dict]:
        return self._pick_cover(locale)

    def list_titles(self) -> list:
        """Titles of every manga that has at least one cover (the only valid answers)."""
        covers = self._get_covers() or {}
        return sorted({info["title"] for info in covers.values() if info.get("title")})

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
        covers_data = self._get_covers()
        if not covers_data:
            return None

        if seed:
            random.seed(seed)

        manga_ids = sorted(list(covers_data.keys()))
        result = None

        for _ in range(50):
            manga_id = random.choice(manga_ids)
            data = covers_data[manga_id]
            locs = [locale] if locale else ["ja", "fr"]
            random.shuffle(locs)

            for loc in locs:
                variant_list = data.get("covers", {}).get(loc, [])
                if variant_list:
                    cover = next(
                        (v for v in variant_list if v.get("volume") == "1"),
                        random.choice(variant_list),
                    )
                    result = {
                        "manga_id": manga_id,
                        "manga_title": data["title"],
                        "cover_url": cover["url"],
                        "locale": loc,
                        "volume": cover.get("volume"),
                        "author": data.get("author"),
                    }
                    break
            if result:
                break

        if seed:
            random.seed(None)
        return result
