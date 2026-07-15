from typing import Any, Dict, List, Optional, Tuple

from ...ports.graph_persistence_port import GraphPersistencePort


class MultiverseService:
    """
    Domain service for handling synthetic universes queries and operations in the Neo4j graph database.
    """

    def __init__(self, neo4j_manager: GraphPersistencePort):
        self.neo4j_manager = neo4j_manager

    def get_gallery_raw_data(self) -> List[Dict[str, Any]]:
        """
        Retrieves all synthetic universes and their associated genres and characters.
        """
        query = """
        MATCH (m:Media {is_synthetic: true})-[:BELONGS_TO]->(g:Genre)
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(m)
        RETURN m, g, collect(c) as characters
        """
        return self.neo4j_manager.execute_query(query)

    def get_catalog_raw_data(
        self,
        search: str = "",
        genre_filter: str = "",
        sort_by: str = "newest",
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Dict[str, Any]], int, List[Dict[str, Any]]]:
        """
        Fetches filterable, paginated, and sorted catalog data for synthetic universes.
        Returns:
            Tuple of (universes_records, total_count, available_genres_records)
        """
        skip = (page - 1) * page_size

        # Build dynamic Cypher query
        where_clauses = ["m.is_synthetic = true"]
        params: Dict[str, Any] = {"skip": skip, "limit": page_size}

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
        genre_results = self.neo4j_manager.execute_query(genre_query) or []

        return results, total, genre_results

    def get_universe_pdf_raw_data(self, universe_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetches universe, characters, and relations raw data for a specific universe.
        Returns None if the universe is not found.
        """
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
            return None

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

        return {
            "media": media,
            "genre": genre,
            "characters": characters,
            "relations": relations,
        }
