import logging
from typing import List, Dict, Any
from pipeline.mlops.graph_healer import run_graph_healer

logger = logging.getLogger("animetix.orchestration")

class GraphHealerService:
    """
    Service de domaine encapsulant l'auto-guérison du graphe.
    """
    def __init__(self):
        pass

    def perform_healing(self, limit: int = 100) -> Dict[str, Any]:
        """
        Exécute l'agent d'auto-guérison et retourne un rapport.
        """
        try:
            logger.info("Starting Graph Healing process...")
            # Note: Le script actuel utilise print, on pourrait wrapper stdout si besoin
            run_graph_healer(limit=limit)
            return {"status": "success", "message": "Healing cycle completed."}
        except Exception as e:
            logger.error(f"Graph Healing process failed: {e}")
            return {"status": "error", "message": str(e)}
