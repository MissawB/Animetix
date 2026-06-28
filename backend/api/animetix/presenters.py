import random

from django.utils.translation import gettext_lazy as _

# Ordered list of every Classic-mode hint key (also the default order/selection).
CLASSIC_HINT_ORDER = [
    "year",
    "origin",
    "tags",
    "genres",
    "studio",
    "letter",
    "words",
    "desc",
]


class ArchetypistPresenter:
    """Helper class to prepare UI data for the Archetypist view."""

    POSITIONS = [
        {"style": "top-[-20px] left-[10%] rotate-[-12deg]", "fly": "fly-top"},
        {"style": "top-[20%] left-[-40px] rotate-[8deg]", "fly": "fly-left"},
        {"style": "bottom-[15%] left-[2%] rotate-[-6deg]", "fly": "fly-left"},
        {"style": "bottom-[-50px] left-[30%] rotate-[15deg]", "fly": "fly-bottom"},
        {"style": "bottom-[5%] right-[25%] rotate-[-10deg]", "fly": "fly-bottom"},
        {"style": "top-[10%] right-[-20px] rotate-[-5deg]", "fly": "fly-right"},
        {"style": "bottom-[25%] right-[-30px] rotate-[12deg]", "fly": "fly-right"},
        {"style": "top-[-40px] right-[20%] rotate-[8deg]", "fly": "fly-top"},
    ]

    CROSS_MEDIA_MAPPING = {
        "Anime": [
            {"label": "Jeux Vidéo", "type": "Game", "icon": "bi-controller"},
            {"label": "Mangas", "type": "Manga", "icon": "bi-book"},
            {"label": "Films", "type": "Movie", "icon": "bi-film"},
        ],
        "Manga": [
            {"label": "Jeux Vidéo", "type": "Game", "icon": "bi-controller"},
            {"label": "Animes", "type": "Anime", "icon": "bi-tv"},
            {"label": "Films", "type": "Movie", "icon": "bi-film"},
        ],
        "Character": [
            {"label": "Acteurs", "type": "Actor", "icon": "bi-person-badge"},
            {"label": "Perso Film", "type": "Movie", "icon": "bi-film"},
            {"label": "Perso Jeux", "type": "Game", "icon": "bi-controller"},
        ],
    }

    @classmethod
    def get_cross_media_options(cls, media_type):
        return cls.CROSS_MEDIA_MAPPING.get(media_type, [])

    @classmethod
    def get_example_covers(cls, pool, limit=8):
        items_with_img = [item for item in pool if item.get("image")]
        if not items_with_img:
            return []

        selected = random.sample(items_with_img, min(len(items_with_img), limit))

        for i, item in enumerate(selected):
            pos = (
                cls.POSITIONS[i]
                if i < len(cls.POSITIONS)
                else {"style": "", "fly": "fly-bottom"}
            )
            item["css_style"] = pos["style"]
            item["fly_class"] = pos["fly"]
            item["animation_delay"] = round((i + 1) * 0.15, 2)

        return selected

    @staticmethod
    def build_forge_items(data_dict, limit=500):
        """Helper to build a clean list for JS (used by the Forge)."""
        items = []
        pool = (
            data_dict.get("lookup", [])
            if data_dict.get("lookup")
            else [{"title": t} for t in data_dict.get("titles", [])]
        )

        title_to_full = data_dict.get("title_to_full_data", {})

        for it in pool:
            title = it.get("title") or it.get("name")
            if not title:
                continue
            full = title_to_full.get(title, {})
            img = it.get("image") or full.get("image")
            if not img:
                continue

            items.append(
                {
                    "title": title,
                    "title_native": it.get("title_native")
                    or full.get("title_native")
                    or full.get("title_jp")
                    or "",
                    "image": img,
                }
            )
            if len(items) >= limit:
                break

        # Fallback if few images found
        if len(items) < 10:
            for it in pool[:limit]:
                title = it.get("title") or it.get("name")
                if not title:
                    continue
                if any(x["title"] == title for x in items):
                    continue
                full = title_to_full.get(title, {})
                items.append(
                    {
                        "title": title,
                        "title_native": it.get("title_native")
                        or full.get("title_native")
                        or full.get("title_jp")
                        or "",
                        "image": it.get("image") or full.get("image") or "",
                    }
                )
                if len(items) >= limit:
                    break
        return items

    @staticmethod
    def get_game_modes(features=None):
        """Centralizes game mode configuration for the UI, supporting Feature Flags."""
        features = features or {}
        experimental = features.get("EXPERIMENTAL_MODES", False)

        modes = {
            "solo": [
                {
                    "titre": _("Classic Mode"),
                    "titre_brush_1": _("CLASSIC"),
                    "titre_brush_2": _("MODE"),
                    "description": _(
                        "Trouvez le titre mystère grâce à la similarité sémantique."
                    ),
                    "url": "start_game",
                    "icon_url": "/static/animetix/img/ui/frieren.png",
                    "gradient": "from-blue-600 via-indigo-500 to-blue-400",
                    "post_only": True,
                },
                {
                    "titre": _("Emoji Decode"),
                    "titre_brush_1": _("EMOJI"),
                    "titre_brush_2": _("DECODE"),
                    "description": _(
                        "Déchiffrez les symboles pour identifier l'œuvre cachée."
                    ),
                    "url": "emoji_decode",
                    "icon_url": "/static/animetix/img/ui/Shaman_king.png",
                    "gradient": "from-orange-600 via-red-500 to-amber-400",
                    "post_only": False,
                },
                {
                    "titre": _("Animinator Oracle"),
                    "titre_brush_1": _("ANIMINATOR"),
                    "titre_brush_2": _("ORACLE"),
                    "description": _(
                        "Posez vos questions à l'Oracle pour débusquer le secret."
                    ),
                    "url": "animinator",
                    "icon_url": "/static/animetix/img/ui/Sinbad.png",
                    "gradient": "from-purple-700 via-violet-600 to-purple-400",
                    "post_only": False,
                },
                {
                    "titre": _("Akinetix Devin"),
                    "titre_brush_1": _("AKINETIX"),
                    "titre_brush_2": _("DEVIN"),
                    "description": _(
                        "L'IA analyse vos pensées pour deviner ce que vous cachez."
                    ),
                    "url": "akinetix",
                    "icon_url": "/static/animetix/img/ui/Saiki.png",
                    "gradient": "from-pink-600 via-rose-500 to-pink-400",
                    "post_only": False,
                },
                {
                    "titre": _("Paradox Quest"),
                    "titre_brush_1": _("PARADOX"),
                    "titre_brush_2": _("QUEST"),
                    "description": _(
                        "Débusquez l'intrus parmi les scénarios générés par l'IA."
                    ),
                    "url": "paradox",
                    "icon_url": "/static/animetix/img/ui/Steins_gate.png",
                    "gradient": "from-red-700 via-rose-600 to-red-400",
                    "post_only": True,
                },
                {
                    "titre": _("Vision Quest"),
                    "titre_brush_1": _("VISION"),
                    "titre_brush_2": _("QUEST"),
                    "description": _(
                        "Défiez la reconnaissance visuelle de l'IA en décrivant l'image."
                    ),
                    "url": "vision_quest",
                    "icon_url": "/static/animetix/img/ui/SAO.png",
                    "gradient": "from-cyan-600 via-blue-500 to-sky-400",
                    "post_only": False,
                },
                {
                    "titre": _("Blind Test"),
                    "titre_brush_1": _("BLIND"),
                    "titre_brush_2": _("TEST"),
                    "description": _(
                        "Devinez l'animé à partir de son opening ou ending."
                    ),
                    "url": "blindtest",
                    "icon_url": "/static/animetix/img/ui/Kaori.png",
                    "gradient": "from-green-600 via-teal-500 to-emerald-400",
                    "post_only": True,
                },
                {
                    "titre": _("Cover Test"),
                    "titre_brush_1": _("COVER"),
                    "titre_brush_2": _("TEST"),
                    "description": _(
                        "Devinez le manga à partir de sa couverture (JA/FR)."
                    ),
                    "url": "covertest",
                    "icon_url": "/static/animetix/img/ui/Bakuman.png",
                    "gradient": "from-amber-600 via-yellow-500 to-orange-400",
                    "post_only": True,
                },
                {
                    "titre": _("Versus Battle"),
                    "titre_brush_1": _("VERSUS"),
                    "titre_brush_2": _("BATTLE"),
                    "description": _(
                        "Simulez un combat d'experts entre deux personnages mythiques."
                    ),
                    "url": "vs_battle",
                    "icon_url": "/static/animetix/img/ui/Naruto_Sasuke.png",
                    "gradient": "from-red-600 via-gray-800 to-black",
                    "post_only": False,
                },
            ],
            "multi": [
                {
                    "titre": _("Undercover"),
                    "description": _("Débusquez l'intrus."),
                    "url": "undercover_party_setup",
                    "icon_url": "/static/animetix/img/ui/Light.png",
                    "is_new": False,
                    "post_only": False,
                },
                {
                    "titre": _("Code Manga"),
                    "description": _("Agents secrets."),
                    "url": "codemanga",
                    "icon_url": "/static/animetix/img/ui/code_manga.png",
                    "is_new": False,
                    "post_only": False,
                },
            ],
            "creative": [
                {
                    "titre": _("Fusion d'Univers"),
                    "titre_sub": _("CRÉEZ DES MONDES UNIQUES À TOUT MOMENT"),
                    "url": "archetypist",
                    "fusion_image": "/static/animetix/img/ui/Fusion.png",
                    "post_only": False,
                },
            ],
            "collections": [
                {
                    "nom": "ANIME",
                    "mode": "Anime",
                    "image": "/static/animetix/img/anime.png",
                },
                {
                    "nom": "MANGA",
                    "mode": "Manga",
                    "image": "/static/animetix/img/manga.png",
                },
                {
                    "nom": "PERSO",
                    "mode": "Character",
                    "image": "/static/animetix/img/perso.png",
                },
            ],
        }

        if not experimental:
            modes["solo"] = [
                m
                for m in modes["solo"]
                if m["url"] not in ["paradox", "vision_quest", "akinetix"]
            ]
            modes["creative"] = []

        if features.get("BETA_SOCIAL"):
            modes["multi"].append(
                {
                    "titre": _("Duels 1vs1"),
                    "description": _("Affrontez un ami en temps réel."),
                    "url": "join_duel",
                    "icon_url": "/static/animetix/img/ui/Naruto_Sasuke.png",
                    "is_new": True,
                    "post_only": False,
                }
            )

        return modes

    @staticmethod
    def get_theme_color(title):
        """Returns a theme color hex code based on the title keywords."""
        title = title.lower()
        mapping = {
            "naruto": "#FF9800",
            "one piece": "#FBC02D",
            "bleach": "#FF5722",
            "hunter x hunter": "#4CAF50",
            "dragon ball": "#0277BD",
            "attack on titan": "#795548",
            "death note": "#212121",
            "demon slayer": "#E91E63",
            "jujutsu kaisen": "#673AB7",
            "frieren": "#80CBC4",
            "mushoku": "#AFB42B",
        }
        for key, color in mapping.items():
            if key in title:
                return color
        return "#fdb913"


class GamePresenter:
    """Helper class to format game-related data for the UI."""

    @staticmethod
    def get_score_color(score: float) -> str:
        """Returns a Tailwind color class based on the similarity score."""
        from core.domain.services.scoring_service import (  # noqa: E402
            ScoringDomainService,
        )

        return ScoringDomainService.get_ui_score_color_class(score)

    @staticmethod
    def format_hint(
        h_type: str,
        label: str,
        unlock_at: int,
        value: str,
        guess_count: int,
        revealed_ids: list,
    ) -> dict:
        """Formats a hint configuration for the UI."""
        can_reveal = guess_count >= unlock_at
        is_revealed = h_type in revealed_ids
        return {
            "label": label,
            "unlocks_at": unlock_at,
            "can_reveal": can_reveal,
            "revealed": is_revealed,
            "value": value if is_revealed else None,
        }

    @classmethod
    def format_classic_hints(
        cls,
        secret_data: dict,
        guess_count: int,
        revealed_ids: list,
        hint_config: "list | None" = None,
        step: int = 5,
    ) -> dict:
        """Centralizes hint formatting for the Classic mode.

        ``hint_config`` is an ordered list of hint keys chosen by the player
        (which hints, and in which order). Unlock thresholds follow that order:
        the n-th hint unlocks after ``n * step`` guesses. ``None`` falls back to
        the full default order; an empty list yields no hints (Tryhard mode).
        """
        if not secret_data:
            secret_data = {}

        # Metadata is flattened onto the item by the repository, but fall back to a
        # nested "metadata" dict for catalogs built from raw files.
        meta = secret_data.get("metadata")
        meta = meta if isinstance(meta, dict) else {}

        def field(key):
            value = secret_data.get(key)
            return value if value not in (None, "") else meta.get(key)

        def fmt_list(val, n=5):
            """Join a list of strings/objects into a short readable string."""
            if not isinstance(val, list) or not val:
                return None
            out = []
            for x in val[:n]:
                if isinstance(x, dict):
                    out.append(x.get("name") or x.get("title") or "")
                else:
                    out.append(str(x))
            out = [o for o in out if o]
            return ", ".join(out) if out else None

        title = str(secret_data.get("title") or "")

        year = field("year")
        year_str = str(year) if year else "Inconnu"

        origin = field("origin") or "Inconnu"

        tags_str = fmt_list(field("tags")) or "Inconnu"
        genres_str = fmt_list(field("genres")) or "Inconnu"

        studios = field("studios")
        studio_str = (
            fmt_list(studios)
            or (studios if isinstance(studios, str) else None)
            or field("studio")
            or "Inconnu"
        )

        letter = title[:1].upper() or "?"
        word_count = len(title.split())
        words_str = f"{word_count} mot" + ("s" if word_count > 1 else "")

        desc = (
            secret_data.get("description")
            or field("clean_description")
            or field("synopsis_fr")
            or "..."
        )
        desc_snippet = desc[:100] + "..." if len(desc) > 100 else desc

        catalog = {
            "year": ("Année de sortie", year_str),
            "origin": ("Origine", origin),
            "tags": ("Tags", tags_str),
            "genres": ("Genres", genres_str),
            "studio": ("Studio", studio_str),
            "letter": ("Première lettre", letter),
            "words": ("Nombre de mots", words_str),
            "desc": ("Description", desc_snippet),
        }

        # None means "not configured" → default selection. An explicit empty
        # list means "no hints" (Tryhard mode) and is preserved as such.
        if hint_config is None:
            hint_config = CLASSIC_HINT_ORDER
        order = list(dict.fromkeys(k for k in hint_config if k in catalog))

        result = {}
        for i, key in enumerate(order):
            label, value = catalog[key]
            result[key] = cls.format_hint(
                key, label, (i + 1) * step, value, guess_count, revealed_ids
            )
        return result
