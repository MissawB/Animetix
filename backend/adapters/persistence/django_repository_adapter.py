import logging
from typing import List, Dict, Optional, Any
from django.conf import settings
from core.ports.repository_port import RepositoryPort
from animetix.models import MediaItem
from django.db.models import Q

logger = logging.getLogger('animetix')

_alloydb_nl_supported = None

def is_alloydb_nl_query_supported() -> bool:
    global _alloydb_nl_supported
    if _alloydb_nl_supported is not None:
        return _alloydb_nl_supported
        
    from django.db import connection
    if connection.vendor != 'postgresql':
        _alloydb_nl_supported = False
        return False
        
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc p 
                    JOIN pg_namespace n ON p.pronamespace = n.oid 
                    WHERE n.nspname = 'alloydb_ai_nl' AND p.proname = 'get_sql'
                );
            """)
            row = cursor.fetchone()
            _alloydb_nl_supported = bool(row and row[0])
    except Exception as e:
        logger.warning(f"[AlloyDB AI] Failed to probe alloydb_ai_nl.get_sql function: {e}")
        _alloydb_nl_supported = False
    return _alloydb_nl_supported

class DjangoRepositoryAdapter(RepositoryPort):
    def get_nearest_neighbors(self, collection_name: str, item_id: str, n_results: int = 5) -> List[Dict]:
        """Désactivé dans l'adaptateur relationnel. Utiliser ChromaDB."""
        return []

    def load_catalog(self, media_type: str) -> Optional[Dict]:
        items = MediaItem.objects.filter(media_type=media_type)
        return {
            'lookup': [self._to_dict(item) for item in items],
            'title_to_full_data': {item.title: self._to_dict(item) for item in items}
        }

    def load_themes(self) -> Dict:
        return {}

    def load_covers(self) -> Dict:
        return {}

    def calculate_similarity(self, collection_name: str, item_a_id: str, item_b_id: str) -> float:
        """Désactivé dans l'adaptateur relationnel. Utiliser ChromaDB."""
        return 0.0

    def upsert_items(self, collection_name: str, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: Optional[List[str]] = None):
        """Upsert les items dans Django (ignore les embeddings)."""
        for i, external_id in enumerate(ids):
            MediaItem.objects.update_or_create(
                external_id=external_id,
                defaults={"metadata": metadatas[i]}
            )

    def delete_collection(self, collection_name: str):
        """Désactivé."""
        pass

    def get_collection_count(self, collection_name: str) -> int:
        """Désactivé."""
        return 0

    def get_all_ids(self, collection_name: str) -> List[str]:
        """Désactivé."""
        return []

    def get_media_item(self, media_type: str, external_id: str) -> Optional[Dict]:
        try:
            item = MediaItem.objects.get(media_type=media_type, external_id=external_id)
            return self._to_dict(item)
        except MediaItem.DoesNotExist:
            return None

    def get_catalog_by_type(self, media_type: str, limit: int = 2000, offset: int = 0) -> List[Dict]:
        items = MediaItem.objects.filter(media_type=media_type).order_by('-popularity')[offset:offset+limit]
        return [self._to_dict(item) for item in items]

    def search_media_items(self, query: str, media_type: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict]:
        qs = MediaItem.objects.filter(
            Q(title__icontains=query) | 
            Q(title_english__icontains=query) | 
            Q(title_native__icontains=query)
        )
        if media_type:
            qs = qs.filter(media_type=media_type)
        
        items = qs.order_by('-popularity')[offset:offset+limit]
        return [self._to_dict(item) for item in items]

    def load_latent_space(self, media_type: str, vibe_type: str) -> Optional[List[Dict]]:
        from animetix.models import LatentSpacePoint
        points = LatentSpacePoint.objects.filter(media_type=media_type.lower(), vibe_type=vibe_type.lower())
        if not points.exists():
            return None
        return [
            {
                'x': p.x, 'y': p.y, 'z': p.z,
                'title': p.title, 'external_id': p.external_id,
                'cluster': p.cluster, 'metadata': p.metadata
            } for p in points
        ]

    def sync_latent_space(self, media_type: str, vibe_type: str, data: List[Dict]) -> int:
        from animetix.models import LatentSpacePoint
        media_type = media_type.lower()
        vibe_type = vibe_type.lower()
        
        LatentSpacePoint.objects.filter(media_type=media_type, vibe_type=vibe_type).delete()
        
        objs = []
        for d in data:
            objs.append(LatentSpacePoint(
                media_type=media_type,
                vibe_type=vibe_type,
                external_id=str(d.get('external_id') or d.get('id', '')),
                title=d.get('title') or d.get('name', 'Unknown'),
                x=d.get('x', 0.0),
                y=d.get('y', 0.0),
                z=d.get('z', 0.0),
                cluster=d.get('cluster', 0),
                metadata=d.get('metadata', {})
            ))
        
        created = LatentSpacePoint.objects.bulk_create(objs, batch_size=500)
        return len(created)

    def get_creative_fusion(self, fusion_id: int) -> Optional[Dict]:
        from animetix.models import CreativeFusion
        try:
            fusion = CreativeFusion.objects.get(id=fusion_id)
            return {
                "id": fusion.id,
                "title_a": fusion.title_a,
                "title_b": fusion.title_b,
                "scenario": fusion.scenario_text,
                "image": fusion.image_url,
                "art_style": fusion.art_style
            }
        except Exception:
            return None

    def get_user_gameplay_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        from animetix.models import GameplaySession
        sessions = GameplaySession.objects.filter(user_id=user_id).order_by('-created_at')[:limit]
        return [{"target": s.target_item, "media_type": s.media_type, "won": s.was_won} for s in sessions]

    def get_user_creative_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        from animetix.models import CreativeFusion
        fusions = CreativeFusion.objects.filter(creator_id=user_id).order_by('-created_at')[:limit]
        return [{"art_style": f.art_style, "titles": f"{f.title_a} x {f.title_b}"} for f in fusions]

    def query_data_natural_language(self, query: str, llm_service: Optional[Any] = None) -> List[Dict]:
        from django.db import connection
        from core.utils.sql_guard import validate_sql_query
        
        nl_query_active = getattr(settings, 'ALLOYDB_NL_QUERY_ACTIVE', False)
        config_name = getattr(settings, 'ALLOYDB_NL_CONFIG_NAME', 'animetix_catalog')
        
        generated_sql = None
        
        if nl_query_active and is_alloydb_nl_query_supported():
            try:
                with connection.cursor() as cursor:
                    # Native AlloyDB AI call
                    cursor.execute("SELECT alloydb_ai_nl.get_sql(%s, %s) ->> 'sql';", [config_name, query])
                    row = cursor.fetchone()
                    if row:
                        generated_sql = row[0]
            except Exception as e:
                logger.error(f"[AlloyDB AI] Text-to-SQL error using native function: {e}")
                
        # Fallback to local LLM if native didn't execute or failed
        if not generated_sql:
            if not llm_service:
                logger.error("Text-to-SQL Fallback: No LLM service provided to generate query.")
                return []
                
            prompt = f"""You are a PostgreSQL Text-to-SQL expert. 
Generate a valid SQL SELECT query to answer this request: "{query}"

Schema:
Table: animetix_mediaitem
Columns:
- id (integer, primary key)
- external_id (varchar)
- media_type (varchar: 'Anime', 'Manga', 'Character', 'Game', 'Actor', 'Movie')
- title (varchar)
- title_english (varchar)
- title_native (varchar)
- synopsis_en (text)
- synopsis_fr (text)
- alternative_titles (json)
- description (text)
- image_url (varchar)
- release_year (integer)
- rating (float)
- popularity (float)
- metadata (json)

Strict Guidelines:
1. Target ONLY the table `animetix_mediaitem`.
2. Return ONLY the raw SQL query. Do not wrap it in markdown code blocks, do not write explanations.
3. Keep the query simple and direct.
"""
            try:
                generated_sql = llm_service.generate(prompt, system_prompt="You are a SQL generator. Output only raw SQL.")
                if generated_sql:
                    generated_sql = generated_sql.strip()
                    # Strip any markdown backticks if the LLM outputted them despite instructions
                    if generated_sql.startswith("```sql"):
                        generated_sql = generated_sql[6:]
                    if generated_sql.startswith("```"):
                        generated_sql = generated_sql[3:]
                    if generated_sql.endswith("```"):
                        generated_sql = generated_sql[:-3]
                    generated_sql = generated_sql.strip()
            except Exception as e:
                logger.error(f"Text-to-SQL Fallback: LLM query generation failed: {e}")
                return []
                
        if not generated_sql:
            logger.error("Text-to-SQL: Failed to produce SQL query.")
            return []
            
        # Security validation
        if not validate_sql_query(generated_sql):
            logger.error(f"SQL Guardrail: Rejected SQL query: {generated_sql}")
            return []
            
        # Execute query
        try:
            with connection.cursor() as cursor:
                cursor.execute(generated_sql)
                # Fetch column names
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
            results = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                results.append(row_dict)
            return results
        except Exception as e:
            logger.error(f"Text-to-SQL: Database execution failed for query '{generated_sql}': {e}")
            return []

    def _to_dict(self, item: MediaItem) -> Dict:
        data = {
            'id': item.external_id,
            'title': item.title,
            'title_english': item.title_english,
            'title_native': item.title_native,
            'description': item.description,
            'synopsis_en': item.synopsis_en,
            'synopsis_fr': item.synopsis_fr,
            'alternative_titles': item.alternative_titles,
            'image': item.image_url,
            'year': item.release_year,
            'popularity': item.popularity,
            'rating': item.rating
        }
        if item.metadata:
            data.update(item.metadata)
        return data
