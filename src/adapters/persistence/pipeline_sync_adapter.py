import requests
import os
import sys
import logging
from typing import Dict
from core.ports.sync_port import SyncPort

logger = logging.getLogger('animetix')

class PipelineSyncAdapter(SyncPort):
    def __init__(self, brain_api_url: str):
        self.brain_api_url = brain_api_url

    def sync_to_vector_db(self, media_type: str, item_id: str, data: Dict):
        logger.info(f"📡 Requesting re-vectorization for {media_type} {item_id}")

    def sync_to_graph_db(self, media_type: str, item_id: str, data: Dict):
        try:
            # On cherche le client neo4j dans le dossier src/pipeline
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            src_path = os.path.join(project_root, "src")
            if src_path not in sys.path:
                sys.path.append(src_path)
            
            from pipeline.neo4j_client import neo4j_manager
            neo4j_manager.sync_media_to_graph(data, media_type)
            logger.info(f"✅ Synced {media_type} {item_id} to Neo4j.")
        except Exception as e:
            logger.error(f"❌ Sync Graph Error for {media_type} {item_id}: {e}")
