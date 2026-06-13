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
            for j, seg in enumerate(segments):
                chunk_id = f"{video_id}_{i}_{j}"
                emb = seg.get("embedding", [])
                
                # Only index if we have a valid embedding
                if emb:
                    ids.append(chunk_id)
                    embeddings.append(emb)
                    metadatas.append({
                        "video_id": video_id,
                        "chunk_index": i,
                        "segment_index": j,
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
        """
        Découpe la vidéo en segments valides.
        NOTE: Cette version utilise un ré-encodage via imageio pour garantir 
        que chaque segment est un fichier MP4 lisible par le VLM.
        """
        import imageio
        import tempfile
        import os
        import numpy as np

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
                tmp_in.write(video_data)
                tmp_in_path = tmp_in.name

            reader = imageio.get_reader(tmp_in_path)
            meta = reader.get_meta_data()
            fps = meta.get('fps', 24)

            # On découpe en 4 segments temporels pour la démo industrielle
            all_frames = list(reader)
            reader.close()
            os.unlink(tmp_in_path)

            num_frames = len(all_frames)
            if num_frames == 0:
                return [video_data]

            chunk_size = num_frames // 4
            chunks = []

            for i in range(4):
                start = i * chunk_size
                end = (i + 1) * chunk_size if i < 3 else num_frames
                segment_frames = all_frames[start:end]

                if not segment_frames:
                    continue

                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                    tmp_out_path = tmp_out.name
                    # Note: we use a standard codec compatible with most VLMs
                    writer = imageio.get_writer(tmp_out_path, fps=fps, codec='libx264')
                    for frame in segment_frames:
                        writer.append_data(frame)
                    writer.close()

                    with open(tmp_out_path, "rb") as f:
                        chunks.append(f.read())
                    os.unlink(tmp_out_path)

            return chunks if chunks else [video_data]
        except Exception as e:
            logger.warning(f"Fallback to byte-slicing due to re-encoding failure: {e}")
            size = len(video_data)
            if size == 0: return []
            return [
                video_data[0 : size//4],
                video_data[size//4 : size//2],
                video_data[size//2 : 3*size//4],
                video_data[3*size//4 : ]
            ]
