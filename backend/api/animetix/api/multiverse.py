from dependency_injector.wiring import Provide, inject
from rest_framework.response import Response
from rest_framework.views import APIView

from ..containers import Container


class MultiverseGalleryView(APIView):
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
