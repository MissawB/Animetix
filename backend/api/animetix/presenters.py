import io
import random

from django.utils.translation import gettext_lazy as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#7F8C8D"))
        self.drawString(40, 30, "Animetix Multiverse — Fiche Scénaristique Wiki")
        self.drawRightString(
            A4[0] - 40, 30, f"Page {self._pageNumber} sur {page_count}"
        )

        # Header (except first page)
        if self._pageNumber > 1:
            self.drawString(40, A4[1] - 30, "Animetix Multiverse Catalog")
            self.setStrokeColor(colors.HexColor("#BDC3C7"))
            self.setLineWidth(0.5)
            self.line(40, A4[1] - 34, A4[0] - 40, A4[1] - 34)

        self.restoreState()


class MultiversePresenter:
    """Helper class to format Multiverse data (JSON/PDF) for the UI."""

    @staticmethod
    def format_gallery_data(results: list) -> dict:
        nodes = []
        links = []
        genres_added = set()
        universes_added = set()

        for record in results:
            media = record.get("m")
            genre = record.get("g")
            characters = record.get("characters", [])

            if not media or not genre:
                continue

            genre_name = genre.get("name")
            genre_id = f"genre_{genre_name}"

            if genre_id not in genres_added:
                nodes.append(
                    {"id": genre_id, "name": genre_name, "type": "genre", "val": 15}
                )
                genres_added.add(genre_id)

            universe_name = media.get("name") or media.get("title")
            if universe_name not in universes_added:
                nodes.append(
                    {
                        "id": universe_name,
                        "name": universe_name,
                        "type": "universe",
                        "val": 10,
                        "metadata": {
                            "description": media.get("description"),
                            "cosmology": media.get("cosmology"),
                            "characters": [c.get("name") for c in characters],
                        },
                    }
                )
                universes_added.add(universe_name)

                links.append({"source": universe_name, "target": genre_id})

        return {"nodes": nodes, "links": links}

    @staticmethod
    def format_catalog_data(
        results: list,
        total: int,
        page: int,
        page_size: int,
        search: str,
        genre_filter: str,
        sort_by: str,
        genre_results: list,
    ) -> dict:
        available_genres = (
            [{"name": r.get("name"), "count": r.get("count", 0)} for r in genre_results]
            if genre_results
            else []
        )

        universes = []
        for record in results:
            media = record.get("media", {})
            genre = record.get("genre", {})
            characters = record.get("characters", [])
            char_count = record.get("char_count", 0)

            universes.append(
                {
                    "id": media.get("name") or media.get("title", "unknown"),
                    "name": media.get("name") or media.get("title", "Univers Inconnu"),
                    "description": media.get("description", ""),
                    "cosmology": media.get("cosmology", ""),
                    "genre": genre.get("name", "Unknown"),
                    "is_synthetic": True,
                    "character_count": char_count,
                    "characters": [
                        {
                            "name": c.get("name", "Unknown"),
                            "role": c.get("role", ""),
                            "power_level": c.get("power_level", 0),
                        }
                        for c in characters[:8]
                    ],
                    "created_at": media.get("created_at"),
                }
            )

        return {
            "results": universes,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": max(1, -(-total // page_size)),  # Ceil division
                "has_next": (page * page_size) < total,
                "has_previous": page > 1,
            },
            "filters": {
                "search": search,
                "genre": genre_filter,
                "sort": sort_by,
            },
            "available_genres": available_genres,
        }

    @staticmethod
    def generate_lore_pdf(universe_name: str, raw_data: dict) -> io.BytesIO:
        media = raw_data.get("media", {})
        genre = raw_data.get("genre", {})
        characters = raw_data.get("characters", [])
        relations = raw_data.get("relations", [])

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()

        # Custom Styles for Wiki Theme
        primary_color = colors.HexColor("#2C3E50")  # Slate Blue
        secondary_color = colors.HexColor("#16A085")  # Teal
        text_color = colors.HexColor("#34495E")  # Charcoal
        bg_light = colors.HexColor("#F8F9F9")  # Off white / Light gray

        title_style = ParagraphStyle(
            "WikiTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=primary_color,
            spaceAfter=10,
        )

        h2_style = ParagraphStyle(
            "WikiH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=secondary_color,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "WikiBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=text_color,
            spaceAfter=6,
        )

        meta_style = ParagraphStyle(
            "WikiMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#7F8C8D"),
            spaceAfter=12,
        )

        th_style = ParagraphStyle(
            "WikiTH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=colors.white,
        )

        td_style = ParagraphStyle(
            "WikiTD",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=text_color,
        )

        story = []

        # Title
        story.append(
            Paragraph(
                media.get("name") or media.get("title", "Univers Fictif"), title_style
            )
        )
        genre_name = genre.get("name") if genre else "Inconnu"
        story.append(
            Paragraph(
                f"Genre Principal : <b>{genre_name}</b> | Univers Synthétique Animetix",
                meta_style,
            )
        )

        # Divider line
        divider = Table([[""]], colWidths=[doc.width], rowHeights=[1.5])
        divider.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), secondary_color),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(divider)
        story.append(Spacer(1, 10))

        # Description Section
        story.append(Paragraph("Description Générale", h2_style))
        desc_text = (
            media.get("description")
            or "Aucune description de lore n'a été spécifiée pour cet univers."
        )
        story.append(Paragraph(desc_text, body_style))

        # Cosmology Section
        story.append(Paragraph("Cosmologie & Lois Physiques", h2_style))
        cosmo_text = (
            media.get("cosmology")
            or "Les lois cosmologiques de cet univers n'ont pas encore été archivées."
        )
        story.append(Paragraph(cosmo_text, body_style))

        # Characters Section
        story.append(Paragraph("Personnages Clés de l'Univers", h2_style))
        if characters:
            char_data = [
                [
                    Paragraph("<b>Nom</b>", th_style),
                    Paragraph("<b>Rôle / Description</b>", th_style),
                    Paragraph("<b>Puissance</b>", th_style),
                ]
            ]
            for char in characters:
                c_name = char.get("name", "Inconnu")
                c_role = char.get("role", "Rôle inconnu")
                c_power = str(char.get("power_level", "N/A"))
                char_data.append(
                    [
                        Paragraph(c_name, td_style),
                        Paragraph(c_role, td_style),
                        Paragraph(c_power, td_style),
                    ]
                )

            # Table configuration
            char_table = Table(char_data, colWidths=[120, 290, 80])
            char_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), secondary_color),
                        ("BACKGROUND", (0, 1), (-1, -1), bg_light),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [bg_light, colors.white]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(char_table)
        else:
            story.append(
                Paragraph("Aucun personnage répertorié dans cet univers.", body_style)
            )

        # Neo4j Relations Section
        story.append(Paragraph("Concepts Clés & Relations Graph (Neo4j)", h2_style))
        if relations:
            rel_data = [
                [
                    Paragraph("<b>Source</b>", th_style),
                    Paragraph("<b>Relation</b>", th_style),
                    Paragraph("<b>Cible (Label)</b>", th_style),
                ]
            ]
            for rel in relations:
                props = rel.get("properties", {})
                labels = rel.get("labels", [])
                target_label = labels[0] if labels else "Entity"
                target_name = props.get("name") or props.get("title") or "Concept"
                rel_type = rel.get("rel_type", "RELATED_TO")
                is_out = rel.get("is_outgoing", True)

                if is_out:
                    src = media.get("name") or media.get("title") or "Univers"
                    tgt = f"{target_name} ({target_label})"
                else:
                    src = f"{target_name} ({target_label})"
                    tgt = media.get("name") or media.get("title") or "Univers"

                rel_data.append(
                    [
                        Paragraph(src, td_style),
                        Paragraph(f"——( {rel_type} )——>", td_style),
                        Paragraph(tgt, td_style),
                    ]
                )

            rel_table = Table(rel_data, colWidths=[180, 130, 180])
            rel_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                        ("BACKGROUND", (0, 1), (-1, -1), bg_light),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [bg_light, colors.white]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(rel_table)
        else:
            story.append(
                Paragraph(
                    "Aucune relation ou concept connexe répertorié dans la base Neo4j.",
                    body_style,
                )
            )

        # Build Document
        doc.build(story, canvasmaker=NumberedCanvas)

        # Seek to start
        buffer.seek(0)
        return buffer
