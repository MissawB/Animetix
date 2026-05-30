import logging
from typing import Dict
from ...ports.sync_port import SyncPort
from ...ports.repository_port import RepositoryPort

logger = logging.getLogger("animetix.sync")

class MediaSyncService:
    def __init__(self, sync_adapter: SyncPort, repository: RepositoryPort):
        self.sync_adapter = sync_adapter
        self.repository = repository

    def handle_media_update(self, media_type: str, item_id: str, data: Dict):
        """Coordonne la synchronisation robuste après une mise à jour PostgreSQL."""
        logger.info(f"🔄 Starting multi-db sync for {media_type} {item_id}")
        
        # 1. Sync Graph (Neo4j)
        try:
            self.sync_adapter.sync_to_graph_db(media_type, item_id, data)
        except Exception as e:
            logger.error(f"❌ Neo4j Sync Failed for {item_id}: {e}")
            raise # Propagate for Celery retry
        
        # 2. Sync Vector (ChromaDB)
        try:
            self.sync_adapter.sync_to_vector_db(media_type, item_id, data)
        except Exception as e:
            logger.error(f"❌ Vector Sync Failed for {item_id}: {e}")
            raise # Propagate for Celery retry

        logger.info(f"✅ Multi-db sync completed for {media_type} {item_id}")
