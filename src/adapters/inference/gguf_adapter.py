import logging
import base64
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from sentence_transformers import CrossEncoder

logger = logging.getLogger("animetix.inference.gguf")

class GgufAdapter(InferencePort):
    def __init__(self, model_path: str, clip_model_path: Optional[str] = None):
        self.model_path = model_path
        self.clip_model_path = clip_model_path
        self.llm = None
        self._cross_encoder = None

    def _load_model(self):
        if self.llm: return
        try:
            from llama_cpp import Llama
            logger.info(f"🏗️ Loading GGUF Model: {self.model_path}")
            
            # Support multimodal if clip_model_path is provided
            kwargs = {
                "model_path": self.model_path,
                "n_ctx": 4096,
                "n_gpu_layers": -1,
                "embedding": True
            }
            if self.clip_model_path:
                logger.info(f"👁️ Enabling Vision support with CLIP: {self.clip_model_path}")
                try:
                    from llama_cpp.llama_chat_format import LlavaChatHandler
                    chat_handler = LlavaChatHandler(clip_model_path=self.clip_model_path)
                    kwargs["chat_handler"] = chat_handler
                except ImportError:
                    logger.warning("LlavaChatHandler not available. Vision support might be limited.")

            self.llm = Llama(**kwargs)
        except ImportError:
            logger.warning("⚠️ llama-cpp-python not installed. GGUFAdapter disabled.")
        except Exception as e:
            logger.error(f"❌ Failed to load GGUF model: {e}")

    def generate(self, prompt: str, system_prompt: str = "Tu es un expert.", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        try:
            self._load_model()
            if not self.llm: return "Erreur: GGUF indisponible."

            if thinking_mode or thinking_budget > 0:
                thinking_instruction = "\n<think>\nAnalyse la requête en profondeur, explore plusieurs pistes et vérifie tes hypothèses avant de répondre.\n</think>"
                system_prompt = f"{system_prompt}{thinking_instruction}"

            max_tokens = 512 + (thinking_budget if thinking_budget > 0 else 0)

            res = self.llm.create_chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return res['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"GGUF Generation Error: {e}")
            return f"Erreur GGUF: {e}"

    def stream_generate(self, prompt: str, system_prompt: str = "Tu es un expert.", thinking_budget: int = 0, thinking_mode: bool = False):
        self._load_model()
        if not self.llm: yield "Erreur: GGUF indisponible."; return

        if thinking_mode or thinking_budget > 0:
            thinking_instruction = "\n<think>\nAnalyse la requête en profondeur, explore plusieurs pistes et vérifie tes hypothèses avant de répondre.\n</think>"
            system_prompt = f"{system_prompt}{thinking_instruction}"

        max_tokens = 512 + (thinking_budget if thinking_budget > 0 else 0)

        stream = self.llm.create_chat_completion(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in stream:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta: yield delta['content']

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise le support Llava de GGUF pour décrire l'image."""
        self._load_model()
        if not self.llm or not self.clip_model_path:
            raise InferenceNotImplementedError("Vision support (CLIP/Llava) not configured for this GgufAdapter.")
        
        try:
            # Encodage de l'image en base64 pour l'API chat completion
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            res = self.llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            )
            return res['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"GGUF Vision Error: {e}")
            return f"Erreur Vision GGUF: {e}"

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        if not documents: return []
        if not self._cross_encoder:
            self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        pairs = [[query, doc] for doc in documents]
        scores = self._cross_encoder.predict(pairs)
        return [float(score) for score in scores]

    def get_text_embedding(self, text: str) -> List[float]:
        try:
            self._load_model()
            if self.llm:
                # Si le modèle supporte les embeddings nativement
                emb = self.llm.create_embedding(text)
                return emb['data'][0]['embedding']
        except Exception:
            pass
        
        # Fallback local
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        return model.encode(text).tolist()

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Simple moderation basée sur des mots-clés pour le mode local."""
        bad_words = ["nsfw", "hantai", "gore", "violence extrême"] 
        detected = [c for c in categories if any(w in text.lower() for w in bad_words)]
        return {
            "is_safe": len(detected) == 0,
            "detected_categories": detected,
            "action": "block" if detected else "allow"
        }

    def health_check(self) -> dict:
        return {
            "status": "online" if self.llm else "offline",
            "engine": "llama.cpp",
            "multimodal": self.clip_model_path is not None
        }

    def _sample_video_frames(self, video_data: bytes, max_frames: int = 8) -> List[bytes]:
        """Helper pour extraire des frames uniformément d'un buffer vidéo."""
        try:
            import imageio
            import tempfile
            import os
            from PIL import Image
            from io import BytesIO
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_data)
                tmp_path = tmp.name
                
            reader = imageio.get_reader(tmp_path)
            meta = reader.get_meta_data()
            fps = meta.get('fps', 24)
            duration = meta.get('duration', 0)
            
            # Calcul des indices de frames pour échantillonnage uniforme
            total_frames = int(duration * fps)
            if total_frames <= 0: total_frames = 1
            indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
            
            frame_bytes_list = []
            for i, frame in enumerate(reader):
                if i in indices:
                    img = Image.fromarray(frame).convert("RGB")
                    buf = BytesIO()
                    img.save(buf, format="JPEG")
                    frame_bytes_list.append(buf.getvalue())
                if len(frame_bytes_list) >= max_frames: break
            
            reader.close()
            os.unlink(tmp_path)
            return frame_bytes_list
        except Exception as e:
            logger.error(f"❌ GGUF Frame sampling failed: {e}")
            return []

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: 
        """
        Localise des actions via analyse image par image (échantillonnage).
        Utilise le support Llava de GGUF pour chaque frame.
        """
        frames_bytes = self._sample_video_frames(video_data)
        if not frames_bytes: return []
        
        all_found_actions = []
        for query in action_queries:
            logger.info(f"🔍 [GGUF] Searching for action: {query}")
            for i, frame_data in enumerate(frames_bytes):
                # On pose une question fermée pour chaque frame
                prompt = f"Is the following action occurring in this image: '{query}'? Answer with YES or NO followed by a brief explanation."
                try:
                    desc = self.generate_image_description(frame_data, prompt)
                    if "YES" in desc.upper():
                        all_found_actions.append({
                            "action": query,
                            "timestamp": i * 2, # Hypothèse 2s entre frames échantillonnées
                            "confidence": 0.75,
                            "explanation": desc
                        })
                except Exception as e:
                    logger.warning(f"GGUF analysis failed for frame {i}: {e}")
                    
        return all_found_actions

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict: 
        """
        Génération de scène 3D via projection de nuage de points (Deterministic Spatial Computing).
        Portable sur GGUF/Local.
        """
        try:
            import numpy as np
            import base64
            from PIL import Image
            from io import BytesIO
            import struct

            rgb = Image.open(BytesIO(image_data)).convert("RGB")
            depth = Image.open(BytesIO(depth_map)).convert("L")
            
            # Redimensionnement pour performance
            rgb = rgb.resize((256, 256))
            depth = depth.resize((256, 256))
            
            rgb_arr = np.array(rgb)
            depth_arr = np.array(depth)
            
            h, w = depth_arr.shape
            points = []
            
            fx, fy = 200.0, 200.0 
            cx, cy = w / 2, h / 2
            
            for y in range(h):
                for x in range(w):
                    z = float(depth_arr[y, x]) / 255.0
                    if z <= 0.05: continue
                    
                    X = (x - cx) * z / fx
                    Y = (y - cy) * z / fy
                    Z = z
                    
                    r, g, b_val = rgb_arr[y, x]
                    points.append((X, Y, Z, r, g, b_val))
            
            header = f"ply\nformat binary_little_endian 1.0\nelement vertex {len(points)}\nproperty float x\nproperty float y\nproperty float z\nproperty uint8 red\nproperty uint8 green\nproperty uint8 blue\nend_header\n"
            
            ply_data = header.encode('ascii')
            for p in points:
                ply_data += struct.pack("<fffBBB", *p)
                
            res_base64 = base64.b64encode(ply_data).decode("utf-8")
            return {
                "status": "success",
                "model_url": f"data:application/octet-stream;base64,{res_base64}",
                "viewer_type": "point_cloud",
                "point_count": len(points)
            }
        except Exception as e:
            logger.error(f"❌ GGUF 3D Scene generation failed: {e}")
            return {"status": "error", "message": str(e)}
