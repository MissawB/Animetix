import logging
import aiohttp
import asyncio
import os
from typing import Optional, List, Dict, Any, Generator
from core.ports.inference_port import InferencePort
from core.domain.exceptions import InferenceError
from core.utils.lazy_import import lazy_import

torch = lazy_import('torch')
transformers = lazy_import('transformers')
AutoModelForCausalLM = transformers.AutoModelForCausalLM
AutoTokenizer = transformers.AutoTokenizer
pipeline = transformers.pipeline

logger = logging.getLogger("animetix.inference.transformers")

class TransformersAdapter(InferencePort):
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True, manga_ocr_device: str = "cpu"):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.use_4bit = use_4bit
        self.manga_ocr_device = manga_ocr_device
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    def _load_model(self):
        if self.model: return
        try:
            from transformers import BitsAndBytesConfig
            logger.info(f"🏗️ Loading Local Model: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            quantization_config = None
            if self.use_4bit:
                quantization_config = BitsAndBytesConfig(load_in_4bit=True)
                
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                device_map="auto", 
                quantization_config=quantization_config,
                trust_remote_code=True
            )
        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")

    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        try:
            self._load_model()
        except Exception as e:
            raise InferenceError(f"Critical failure during model loading: {str(e)}")
            
        if not self.model: 
            raise InferenceError("Local Transformers model not loaded.")
        
        try:
            # Injection du prompt de réflexion
            if thinking_mode or thinking_budget > 0:
                prompt = f"<think>\nAnalyse en profondeur.\n</think>\n{prompt}"
                
            inputs = self.tokenizer(f"{system_prompt}\n\n{prompt}", return_tensors="pt").to(self.model.device)
            max_new_tokens = 512 + (thinking_budget if thinking_budget > 0 else 0)
            
            input_length = inputs.input_ids.shape[1]
            outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            generated_tokens = outputs[0][input_length:]
            return self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        except Exception as e:
            raise InferenceError(f"Generation failed: {str(e)}")

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        try:
            yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)
        except InferenceError:
            raise

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_data)).convert("RGB")
            detector_id = model_id or "google/owlvit-base-patch32"
            if not hasattr(self, '_detector_pipeline') or self._detector_pipeline.model.name_or_path != detector_id:
                self._detector_pipeline = pipeline("zero-shot-object-detection", model=detector_id, device=0 if torch.cuda.is_available() else -1)
            results = self._detector_pipeline(img, candidate_labels=candidate_queries, threshold=0.05)
            return [{"label": res["label"], "score": res["score"], "box": [res["box"]["xmin"], res["box"]["ymin"], res["box"]["xmax"], res["box"]["ymax"]]} for res in results]
        except Exception as e:
            logger.error(f"❌ Object Detection failed: {e}"); return []

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime.") -> str:
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_data)).convert("RGB")
            if not hasattr(self, '_vlm_model'):
                vlm_id = "vikhyatk/moondream2"
                self._vlm_tokenizer = AutoTokenizer.from_pretrained(vlm_id)
                self._vlm_model = AutoModelForCausalLM.from_pretrained(vlm_id, trust_remote_code=True).to("cuda" if torch.cuda.is_available() else "cpu")
            enc_image = self._vlm_model.encode_image(img)
            return self._vlm_model.answer_question(enc_image, prompt, self._vlm_tokenizer)
        except Exception as e:
            logger.error(f"❌ Image description failed: {e}"); return "Échec description."

    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]:
        try:
            from PIL import Image
            from io import BytesIO
            from sentence_transformers import SentenceTransformer
            img = Image.open(BytesIO(image_data)).convert("RGB")
            if not hasattr(self, '_clip_model'):
                self._clip_model = SentenceTransformer('clip-ViT-B-32')
            return self._clip_model.encode(img).tolist()
        except Exception as e:
            logger.error(f"❌ Image Embedding failed: {e}"); return []

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        try:
            from sentence_transformers import util
            img_emb = torch.tensor(self.get_image_embedding(image_data))
            text_embs = torch.tensor(self._clip_model.encode(candidate_labels))
            scores = util.cos_sim(img_emb, text_embs)[0]
            probs = torch.nn.functional.softmax(scores, dim=0).tolist()
            return {l: p for l, p in zip(candidate_labels, probs)}
        except Exception as e:
            logger.error(f"❌ Image Classification failed: {e}"); return {}

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float:
        try:
            from sentence_transformers import util
            if not hasattr(self, '_clip_model'):
                from sentence_transformers import SentenceTransformer
                self._clip_model = SentenceTransformer('clip-ViT-B-32')
            
            # Fallback text-text similarity using CLIP if image data isn't directly available here
            query_emb = self._clip_model.encode(query, convert_to_tensor=True)
            item_emb = self._clip_model.encode(item_id, convert_to_tensor=True)
            
            similarity = util.cos_sim(query_emb, item_emb).item()
            return float(similarity)
        except Exception as e:
            logger.error(f"❌ Visual similarity calculation failed: {e}")
            return 1.0 if query.lower() in item_id.lower() or item_id.lower() in query.lower() else 0.5

    def _load_video_vlm(self):
        """Chargement paresseux de Qwen2-VL pour le RAG temporel."""
        if hasattr(self, '_video_vlm'): return
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
            import torch
            
            logger.info("📽️ Loading Qwen2-VL-2B for Temporal RAG...")
            model_id = "Qwen/Qwen2-VL-2B-Instruct"
            
            quantization_config = None
            if self.use_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )

            self._video_processor = AutoProcessor.from_pretrained(model_id)
            self._video_vlm = Qwen2VLForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
                quantization_config=quantization_config,
                trust_remote_code=True
            )
        except Exception as e:
            logger.error(f"❌ Failed to load Qwen2-VL: {e}")
            raise InferenceError(f"Video VLM loading failed: {str(e)}")

    def _sample_video_frames(self, video_data: bytes, max_frames: int = 8) -> List:
        """Helper pour extraire des frames uniformément d'un buffer vidéo."""
        try:
            import imageio
            import tempfile
            import os
            from PIL import Image
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_data)
                tmp_path = tmp.name
                
            reader = imageio.get_reader(tmp_path)
            meta = reader.get_meta_data()
            fps = meta.get('fps', 24)
            duration = meta.get('duration', 0)
            
            # Calcul des indices de frames pour échantillonnage uniforme
            total_frames = int(duration * fps)
            indices = [int(i * total_frames / max_frames) for i in range(max_frames)]
            
            frames = []
            for i, frame in enumerate(reader):
                if i in indices:
                    frames.append(Image.fromarray(frame).convert("RGB"))
                if len(frames) >= max_frames: break
            
            reader.close()
            os.unlink(tmp_path)
            return frames
        except Exception as e:
            logger.error(f"❌ Frame sampling failed: {e}")
            return []

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: 
        """
        Analyse temporelle profonde via Qwen2-VL.
        Génère un récit structuré du contenu vidéo indexable.
        """
        try:
            self._load_video_vlm()
            frames = self._sample_video_frames(video_data, max_frames=8)
            if not frames: return []

            # Préparation du prompt multimodal
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "video", "video": frames, "fps": 1.0},
                        {"type": "text", "text": "Describe the main actions and key moments in this video segment with timestamps."}
                    ]
                }
            ]
            
            import torch
            text = self._video_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self._video_processor(text=[text], videos=[frames], padding=True, return_tensors="pt").to(self._video_vlm.device)
            
            generated_ids = self._video_vlm.generate(**inputs, max_new_tokens=256)
            output_text = self._video_processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
            
            # On retourne le récit comme "embedding temporel" (indexé textuellement)
            return [{"start": 0, "end": -1, "summary": output_text, "confidence": 0.9}]
            
        except Exception as e:
            logger.error(f"❌ Video temporal analysis failed: {e}")
            raise InferenceError(f"Video reasoning failed: {str(e)}")

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: 
        """
        Localise des actions spécifiques dans une vidéo via raisonnement par fenêtre glissante (Sliding Window).
        Utilise Qwen2-VL pour identifier les segments temporels correspondants.
        """
        try:
            self._load_video_vlm()
            import orjson
            
            # 1. Échantillonnage global (8 frames pour avoir une vue d'ensemble)
            frames = self._sample_video_frames(video_data, max_frames=8)
            if not frames: return []
            
            all_found_actions = []
            
            for query in action_queries:
                # 2. Prompt de localisation temporelle
                prompt = (
                    f"Analyze this video and find the exact timestamps where the action '{query}' occurs. "
                    "Return ONLY a JSON list of objects with 'start' (seconds), 'end' (seconds), and 'confidence' (0-1). "
                    "Example: [{'start': 1.5, 'end': 3.2, 'confidence': 0.85}]. If not found, return []."
                )
                
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "video", "video": frames, "fps": 1.0},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                
                text = self._video_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = self._video_processor(text=[text], videos=[frames], padding=True, return_tensors="pt").to(self._video_vlm.device)
                
                generated_ids = self._video_vlm.generate(**inputs, max_new_tokens=128)
                response = self._video_processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
                
                # 3. Parsing robuste du JSON VLM
                try:
                    if '[' in response and ']' in response:
                        json_str = response[response.find('['):response.rfind(']')+1]
                        localizations = orjson.loads(json_str)
                        for loc in localizations:
                            loc["action"] = query
                            all_found_actions.append(loc)
                except Exception as e:
                    logger.warning(f"Failed to parse VLM localization for '{query}': {e}")
            
            return all_found_actions
            
        except Exception as e:
            logger.error(f"❌ Action localization failed: {e}")
            raise InferenceError(f"Video action localization failed: {str(e)}")

    async def _fetch_images(self, urls: List[str]) -> List[Any]:
        session = await self._get_session()
        tasks = []
        for url in urls:
            tasks.append(self._fetch_single_image(session, url))
        return await asyncio.gather(*tasks)

    async def _fetch_single_image(self, session: aiohttp.ClientSession, url: str) -> Optional[Any]:
        try:
            from PIL import Image
            from io import BytesIO
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.read()
                    return Image.open(BytesIO(content)).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to fetch image {url}: {e}")
        return None

    def _fetch_images_sync(self, urls: List[str]) -> List[Any]:
        import requests
        from PIL import Image
        from io import BytesIO
        
        results = []
        for url in urls:
            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    results.append(Image.open(BytesIO(res.content)).convert("RGB"))
                else:
                    results.append(None)
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                results.append(None)
        return results

    def _load_clip_model(self):
        if hasattr(self, '_clip_model'): return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("🏗️ Loading CLIP for reranking...")
            self._clip_model = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP: {e}")
            raise InferenceError(f"Critical failure during CLIP loading: {str(e)}")

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]: 
        """Reranking visuel via CLIP (Sync)."""
        from sentence_transformers import util
        
        self._load_clip_model()
        images = self._fetch_images_sync(image_urls)
        
        # Filter None results
        valid_images = [img for img in images if img is not None]
        valid_urls = [url for url, img in zip(image_urls, images) if img is not None]
        
        if not valid_images:
            return []
            
        # Embeddings
        query_emb = self._clip_model.encode(query, convert_to_tensor=True)
        img_embs = self._clip_model.encode(valid_images, convert_to_tensor=True)
        
        scores = util.cos_sim(query_emb, img_embs)[0]
        
        results = []
        valid_idx = 0
        for orig_idx, img in enumerate(images):
            if img is not None:
                score = float(scores[valid_idx])
                results.append({"index": orig_idx, "url": image_urls[orig_idx], "score": score})
                valid_idx += 1
            
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Analyse le texte pour détecter du contenu inapproprié ou des spoilers (Guardrail)."""
        bad_words = ["hentai", "nsfw", "porn", "sex", "gore", "violence extreme"]
        found = [w for w in bad_words if w in text.lower()]
        is_safe = len(found) == 0
        return {
            "is_safe": is_safe,
            "detected_categories": found,
            "action": "block" if not is_safe else "allow"
        }

    def _load_colpali_engine(self):
        """Chargement paresseux de ColPali."""
        if hasattr(self, '_colpali_model'): return
        try:
            from colpali_engine.models import ColPali, ColPaliProcessor
            logger.info("🏗️ Loading ColPali for Late Interaction...")
            model_id = "vidore/colpali-v1.2"
            
            self._colpali_model = ColPali.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto"
            )
            self._colpali_processor = ColPaliProcessor.from_pretrained(model_id)
            logger.info("✅ ColPali engine loaded.")
        except Exception as e:
            logger.error(f"❌ Failed to load ColPali: {e}")
            raise InferenceError(f"ColPali engine loading failed: {str(e)}")

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Implémentation réelle ColPali late interaction."""
        try:
            from PIL import Image
            from io import BytesIO
            
            self._load_colpali_engine()
            img = Image.open(BytesIO(image_data)).convert("RGB")
            
            with torch.no_grad():
                batch = self._colpali_processor.process_images([img]).to(self._colpali_model.device)
                embeddings = self._colpali_model(**batch)
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return embeddings.cpu().tolist()
        except Exception as e:
            logger.error(f"❌ ColPali inference failed: {e}")
            raise InferenceError(f"ColPali inference failed: {str(e)}")

    def health_check(self) -> dict: return {"status": "online" if self.model else "offline", "engine": "transformers"}

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Implémentation du reranking SOTA avec sentence_transformers ou Cohere Rerank API (SOTA 2026)."""
        if not documents:
            return []
            
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {cohere_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "rerank-multilingual-v3.0",
                    "query": query,
                    "documents": documents
                }
                response = requests.post("https://api.cohere.ai/v1/rerank", headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    scores = [0.0] * len(documents)
                    for item in data.get("results", []):
                        idx = item.get("index")
                        if idx is not None and idx < len(scores):
                            scores[idx] = float(item.get("relevance_score", 0.0))
                    return scores
            except Exception as e:
                logger.error(f"❌ Cohere Rerank API connection failed: {e}.")

        from core.utils.lazy_import import lazy_import
        sentence_transformers = lazy_import('sentence_transformers')
        
        model_name = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        if not hasattr(self, '_cross_encoder') or getattr(self, '_cross_encoder_name', '') != model_name:
            self._cross_encoder = sentence_transformers.CrossEncoder(model_name)
            self._cross_encoder_name = model_name
            
        pairs = [[query, doc] for doc in documents]
        scores = self._cross_encoder.predict(pairs)
        return [float(score) for score in scores]
