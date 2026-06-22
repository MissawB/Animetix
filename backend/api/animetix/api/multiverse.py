import io

from dependency_injector.wiring import Provide, inject
from django.http import FileResponse, Http404
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..containers import Container


class MultiverseGalleryView(APIView):
    # Public catalogue browsing: GET stays open, writes (if any) require auth.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        neo4j_manager=Provide[Container.persistence.graph_persistence_port],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.neo4j_manager = neo4j_manager

    def get(self, request):
        query = """
        MATCH (m:Media {is_synthetic: true})-[:BELONGS_TO]->(g:Genre)
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(m)
        RETURN m, g, collect(c) as characters
        """
        results = self.neo4j_manager.execute_query(query)

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

        return Response({"nodes": nodes, "links": links})


class MultiverseCatalogView(APIView):
    """
    GET /api/v1/multiverse/catalog/
    Paginated, filterable, searchable catalog of synthetic universes.

    Query params:
      - search: text search on name/description/cosmology
      - genre: filter by genre name (exact match)
      - sort: 'newest' | 'name' | 'characters' (default: newest)
      - page: page number (1-indexed, default: 1)
      - page_size: items per page (default: 12, max: 48)
    """

    # Public catalogue browsing: GET stays open, writes (if any) require auth.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        neo4j_manager=Provide[Container.persistence.graph_persistence_port],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.neo4j_manager = neo4j_manager

    def get(self, request):
        # Parse query params
        search = request.query_params.get("search", "").strip()
        genre_filter = request.query_params.get("genre", "").strip()
        sort_by = request.query_params.get("sort", "newest")
        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = min(48, max(1, int(request.query_params.get("page_size", 12))))
        except (ValueError, TypeError):
            page_size = 12

        skip = (page - 1) * page_size

        # Build dynamic Cypher query
        where_clauses = ["m.is_synthetic = true"]
        params = {"skip": skip, "limit": page_size}

        if search:
            where_clauses.append(
                "(toLower(m.name) CONTAINS toLower($search) "
                "OR toLower(m.description) CONTAINS toLower($search) "
                "OR toLower(m.cosmology) CONTAINS toLower($search))"
            )
            params["search"] = search

        if genre_filter:
            where_clauses.append("toLower(g.name) = toLower($genre_filter)")
            params["genre_filter"] = genre_filter

        where_str = " AND ".join(where_clauses)

        # Sort mapping
        sort_map = {
            "newest": "m.created_at DESC",
            "name": "m.name ASC",
            "characters": "char_count DESC",
        }
        order_clause = sort_map.get(sort_by, "m.created_at DESC")

        # Count query
        count_query = f"""
        MATCH (m:Media)-[:BELONGS_TO]->(g:Genre)
        WHERE {where_str}
        RETURN count(DISTINCT m) as total
        """
        count_result = self.neo4j_manager.execute_query(count_query, params)
        total = count_result[0].get("total", 0) if count_result else 0

        # Main data query
        data_query = f"""
        MATCH (m:Media)-[:BELONGS_TO]->(g:Genre)
        WHERE {where_str}
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(m)
        WITH m, g, collect(DISTINCT c) as characters, count(DISTINCT c) as char_count
        ORDER BY {order_clause}
        SKIP $skip LIMIT $limit
        RETURN m as media, g as genre, characters, char_count
        """
        results = self.neo4j_manager.execute_query(data_query, params)

        # Available genres query (for filter sidebar)
        genre_query = """
        MATCH (m:Media {is_synthetic: true})-[:BELONGS_TO]->(g:Genre)
        RETURN g.name as name, count(m) as count
        ORDER BY count DESC
        """
        genre_results = self.neo4j_manager.execute_query(genre_query)
        available_genres = (
            [{"name": r.get("name"), "count": r.get("count", 0)} for r in genre_results]
            if genre_results
            else []
        )

        # Format results
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

        return Response(
            {
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
        )


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


class MultiverseExportPDFView(APIView):
    """
    GET /api/v1/multiverse/<str:universe_name>/export-pdf/
    Génère et télécharge une fiche scénaristique PDF stylisée comme un Wiki
    contenant la description, la cosmologie, les personnages et les relations Neo4j.
    """

    # Public catalogue browsing: GET stays open, writes (if any) require auth.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @inject
    def __init__(
        self,
        neo4j_manager=Provide[Container.persistence.graph_persistence_port],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.neo4j_manager = neo4j_manager

    def get(self, request, universe_name):
        # 1. Fetch universe details
        query_universe = """
        MATCH (m:Media {name: $name, is_synthetic: true})
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(g:Genre)
        RETURN m as media, g as genre
        """
        res_universe = self.neo4j_manager.execute_query(
            query_universe, {"name": universe_name}
        )
        if not res_universe:
            raise Http404("Univers synthétique non trouvé.")

        media = res_universe[0].get("media", {})
        genre = res_universe[0].get("genre", {})

        # 2. Fetch characters
        query_characters = """
        MATCH (m:Media {name: $name, is_synthetic: true})
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(m)
        RETURN c as character
        """
        res_characters = self.neo4j_manager.execute_query(
            query_characters, {"name": universe_name}
        )
        characters = [r.get("character") for r in res_characters if r.get("character")]

        # 3. Fetch relations from Neo4j (Concepts clés)
        query_relations = """
        MATCH (m:Media {name: $name, is_synthetic: true})-[r]-(n)
        RETURN type(r) as rel_type, labels(n) as labels, properties(n) as properties, startNode(r) = m as is_outgoing
        """
        res_relations = self.neo4j_manager.execute_query(
            query_relations, {"name": universe_name}
        )
        relations = [r for r in res_relations if r.get("properties")]

        # 4. Generate PDF in memory
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

        # Clean file name
        safe_filename = "".join(
            c for c in universe_name if c.isalnum() or c in (" ", "_", "-")
        ).rstrip()
        safe_filename = safe_filename.replace(" ", "_")
        if not safe_filename:
            safe_filename = "multiverse_lore"

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"wiki_{safe_filename}.pdf",
            content_type="application/pdf",
        )
