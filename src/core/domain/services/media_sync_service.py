from typing import Dict
from ...ports.sync_port import SyncPort
from ...ports.repository_port import RepositoryPort
from ...ports.inference_port import InferencePort

class MediaSyncService:
    def __init__(self, sync_adapter: SyncPort, repository: RepositoryPort):
        self.sync_adapter = sync_adapter
        self.repository = repository

    def handle_media_update(self, media_type: str, item_id: str, data: Dict):
        """Coordonne la synchronisation après une mise à jour PostgreSQL."""
        # 1. Sync Graph
        self.sync_adapter.sync_to_graph_db(media_type, item_id, data)
        
        # 2. Trigger Vectorization and Sync (Can be async in production)
        self.sync_adapter.sync_to_vector_db(media_type, item_id, data)
