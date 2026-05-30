import logging
import base64
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from .agents.debate_manager import DebateManager

logger = logging.getLogger("animetix.rag.video")

class VideoRAGService:
    """
    Orchestrateur Video-RAG Industriel.
    Gère l'analyse distribuée de vidéos d'anime via Celery et VLM.
    """
    def __init__(self, inference_engine: InferencePort, repository=None, prompt_manager=None):
        self.inference_engine = inference_engine
        self.repository = repository
        self.prompt_manager = prompt_manager
        self.chunk_duration = 30 # Secondes par segment
        self.collection_name = "video_temporal"

    def index_video(self, video_id: str, video_data: bytes) -> int:
        """Découpe, analyse et indexe une vidéo dans ChromaDB."""
        if not self.repository:
            logger.error("No repository provided for Video-RAG indexing.")
            return 0
            
        chunks = self._segment_video(video_data)
        ids = []
        embeddings = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            segments = self.inference_engine.get_video_temporal_embeddings(chunk)
            for seg in segments:
                chunk_id = f"{video_id}_{i}"
                emb = seg.get("embedding", [])
                
                # Only index if we have a valid embedding
                if emb:
                    ids.append(chunk_id)
                    embeddings.append(emb)
                    metadatas.append({
                        "video_id": video_id,
                        "chunk_index": i,
                        "start": seg.get("start", 0),
                        "end": seg.get("end", -1),
                        "summary": seg.get("summary", "")
                    })
        
        if ids:
            self.repository.upsert_items(self.collection_name, ids, embeddings, metadatas)
            logger.info(f"Indexed {len(ids)} segments for video {video_id}.")
            return len(ids)
        return 0

    def search_video_segment(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche sémantique d'un segment vidéo."""
        if not self.repository:
            return []
        # Uses standard collection search
        return self.repository.search_media_items(query, media_type=self.collection_name, limit=limit)

    def start_distributed_analysis(self, video_data: bytes, query: Optional[str] = None) -> Any:
        """
        Point d'entrée pour l'analyse asynchrone distribuée.
        Découpe la vidéo et lance un groupe de tâches Celery.
        """
        logger.info("🎬 Video-RAG: Initializing distributed analysis workflow...")
        
        # 1. Découpage logique (Simulé ici, en prod utiliserait un wrapper FFmpeg)
        # On divise les octets pour la démo, mais on prépare la structure
        chunks = self._segment_video(video_data)
        
        from backend.animetix.tasks import process_video_chunk_task, aggregate_video_results_task
        from celery import group, chain

        # 2. Création du groupe de tâches (Map)
        task_group = group(
            process_video_chunk_task.s(
                base64.b64encode(chunk).decode('utf-8'), 
                i, 
                len(chunks), 
                query
            ) for i, chunk in enumerate(chunks)
        )

        # 3. Chaînage vers l'agrégation (Reduce)
        workflow = chain(task_group, aggregate_video_results_task.s(original_query=query))
        
        # 4. Lancement
        result = workflow.apply_async()
        return {"task_id": result.id, "status": "started", "chunks": len(chunks)}

    def process_segment(self, segment_data: bytes) -> Dict[str, Any]:
        """Analyse un segment individuel (Exécuté par un worker Celery)."""
        # Extraction du récit pour ce segment
        narrative = self.inference_engine.get_video_temporal_embeddings(segment_data)
        return {
            "narrative": narrative,
            "has_action": "combat" in str(narrative).lower()
        }

    def find_precise_moment(self, video_data: bytes, query: str) -> Dict[str, Any]:
        """Recherche sémantique précise dans un clip."""
        results = self.inference_engine.localize_video_actions(video_data, [query])
        return results[0] if results else {"description": "Non trouvé"}

    def query_long_video(self, analysis_results: List[Dict[str, Any]], query: str) -> str:
        """
        Réduction : Synthétise les résultats de tous les segments via le LLM.
        """
        # Construction du contexte chronologique
        timeline_context = ""
        for res in analysis_results:
            idx = res['index']
            data = res['data']
            ts = res['timestamp_start']
            timeline_context += f"[{ts}s - {ts+30}s] : {data.get('narrative') or data.get('description')}\n"

        # Appel au LLM pour la synthèse finale
        if self.prompt_manager:
            prompt, system = self.prompt_manager.get_prompt(
                "video_rag_synthesis",
                query=query,
                context=timeline_context
            )
            return self.inference_engine.generate(prompt, system_prompt=system)
        
        return f"Synthèse simplifiée pour '{query}' basée sur {len(analysis_results)} segments."

    def process_long_video(self, video_data: bytes) -> Dict[str, Any]:
        """Orchestration de bout en bout de l'analyse d'une longue vidéo (Sync)."""
        narrative = self.inference_engine.get_video_temporal_embeddings(video_data)
        actions = self.inference_engine.localize_video_actions(video_data, [""])
        return {
            "narrative": narrative,
            "actions": actions
        }

    def _segment_video(self, video_data: bytes) -> List[bytes]:
        """Découpage physique du flux. (En prod: FFmpeg)"""
        # Pour le prototype industriel, on divise en 4 pour montrer le parallélisme
        size = len(video_data)
        return [
            video_data[0 : size//4],
            video_data[size//4 : size//2],
            video_data[size//2 : 3*size//4],
            video_data[3*size//4 : ]
        ]
