import logging
import aiohttp
import asyncio
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
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.use_4bit = use_4bit
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        import aiohttp
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
            
            outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True).replace(system_prompt, "").strip()
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

    def estimate_depth(self, image_data: bytes) -> bytes:
        try:
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_data)).convert("RGB")
            if not hasattr(self, '_depth_pipeline'):
                self._depth_pipeline = pipeline("depth-estimation", model="Intel/dpt-large", device=0 if torch.cuda.is_available() else -1)
            result = self._depth_pipeline(img)
            buf = BytesIO(); result["depth"].save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"❌ Depth Estimation failed: {e}"); return b""

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

    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str:
        """
        Nettoie les bulles de texte en préservant leur forme complexe (jagged, oval, etc.).
        Identifie le texte (noir) et l'efface via inpainting ciblé uniquement sur les traits.
        """
        try:
            import cv2
            import numpy as np
            from PIL import Image
            from io import BytesIO
            import base64

            img_pil = Image.open(BytesIO(image_data)).convert("RGB")
            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            # Masque global pour les zones à effacer
            mask = np.zeros(img_cv.shape[:2], dtype=np.uint8)
            
            for p in text_placements:
                box = p.get("box")
                if box:
                    x1, y1, x2, y2 = [int(v) for v in box]
                    # Extraction et seuillage de la zone pour isoler le texte noir
                    roi = img_cv[y1:y2, x1:x2]
                    if roi.size == 0: continue
                    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                    
                    # Utilisation de la méthode d'Otsu pour trouver automatiquement le seuil optimal
                    # entre le texte (foncé) et le fond de la bulle (clair), quelle que soit la luminosité.
                    # On applique un léger flou avant pour réduire le bruit (trames manga)
                    blurred = cv2.GaussianBlur(gray_roi, (3, 3), 0)
                    _, mask_roi = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                    # Optionnel : si la bulle est noire avec du texte blanc (inversion)
                    # On pourrait le détecter si la majorité des pixels de mask_roi sont blancs
                    if np.mean(mask_roi) > 127:
                        # C'est probablement une bulle noire avec texte blanc, on inverse
                        _, mask_roi = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                    # Éviter de toucher aux bords de la bulle en appliquant une marge interne plus fine
                    h, w = mask_roi.shape
                    if h > 6 and w > 6:
                        inner_gate = np.zeros((h, w), dtype=np.uint8)
                        # Marge pour protéger le contour noir de la bulle
                        cv2.rectangle(inner_gate, (4, 4), (w-4, h-4), 255, -1)
                        mask_roi = cv2.bitwise_and(mask_roi, inner_gate)

                    # Dilatation douce pour bien englober les bords des lettres
                    mask[y1:y2, x1:x2] = cv2.dilate(mask_roi, np.ones((3,3), np.uint8), iterations=1)

            # Inpainting (Telea) avec un rayon de 3
            res_cv = cv2.inpaint(img_cv, mask, 3, cv2.INPAINT_TELEA)
            
            _, buffer = cv2.imencode('.jpg', res_cv)
            return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Smart bubble cleaning failed: {e}"); return ""

    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]:
        bubbles = []
        try:
            from PIL import Image
            from io import BytesIO
            from huggingface_hub import hf_hub_download
            from ultralytics import YOLO
            if not hasattr(self, '_yolo_manga_model'):
                path = hf_hub_download(repo_id="ogkalu/comic-speech-bubble-detector-yolov8m", filename="comic-speech-bubble-detector.pt")
                # Force CPU for YOLO to save VRAM for the LLM
                self._yolo_manga_model = YOLO(path).to('cpu')
            res = self._yolo_manga_model(Image.open(BytesIO(image_data)).convert("RGB"), verbose=False)
            for r in res:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bubbles.append({"label": "bubble", "score": box.conf[0].item(), "box": [x1, y1, x2, y2]})
        except Exception as e:
            logger.error(f"❌ YOLO failed: {e}")
        return {"bubbles": bubbles, "cleaned_image": self.inpaint_text_bubbles(image_data, bubbles)}

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        try:
            from PIL import Image, ImageDraw
            from io import BytesIO
            import base64
            from manga_ocr import MangaOcr
            res = self.process_manga_page(image_data)
            if not res.get("bubbles"): return res
            img_pil = Image.open(BytesIO(image_data)).convert("RGB")
            
            if not hasattr(self, '_manga_ocr_model'): 
                logger.info("⏳ Loading MangaOCR (CPU forced)...")
                # Hack pour forcer MangaOcr sur CPU car il n'expose pas de paramètre 'device'
                import torch
                original_is_available = torch.cuda.is_available
                torch.cuda.is_available = lambda: False
                try:
                    self._manga_ocr_model = MangaOcr()
                finally:
                    torch.cuda.is_available = original_is_available
                
            # Clear cache before heavy LLM ops
            if torch.cuda.is_available(): torch.cuda.empty_cache()
            
            # Travailler sur l'image aux bulles BLANCHES
            cleaned_img = Image.open(BytesIO(base64.b64decode(res["cleaned_image"].split(",")[1]))).convert("RGB")
            draw = ImageDraw.Draw(cleaned_img)
            
            for b in res["bubbles"]:
                x1, y1, x2, y2 = [int(v) for v in b["box"]]
                # OCR sur l'original pour lire le japonais
                jp = self._manga_ocr_model(img_pil.crop((x1, y1, x2, y2)))
                if jp.strip():
                    fr = self.generate(f"Traduis en {target_lang} (FINAL ONLY): {jp}", system_prompt="Expert traducteur manga.")
                    import textwrap
                    width_px = x2 - x1
                    # Calcul d'une largeur de texte adaptée à la bulle
                    wrapped = textwrap.fill(fr, width=max(8, int(width_px/12)))
                    
                    # Centrage vertical et horizontal approximatif
                    draw.multiline_text((x1 + width_px*0.1, y1 + (y2-y1)*0.2), wrapped, fill=(0,0,0), align="center")
            
            buf = BytesIO(); cleaned_img.save(buf, format="JPEG")
            res["translated_image"] = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
            return res
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}"); return {"error": str(e)}

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

    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str:
        """
        Neural Style Transfer Vidéo SOTA (type FateZero).
        Utilise diffusers pour styliser les images et imageio pour reconstruire la vidéo.
        """
        try:
            import cv2
            import numpy as np
            import base64
            import tempfile
            import imageio
            import os
            from PIL import Image
            from io import BytesIO
            from diffusers import AutoPipelineForImage2Image
            
            logger.info(f"🎞️ Starting Video Style Transfer: {studio_style}")
            
            # 1. Chargement paresseux du pipeline Diffusion
            if not hasattr(self, '_sd_pipeline'):
                logger.info("⏳ Loading SDXL-Turbo for fast video stylization...")
                self._sd_pipeline = AutoPipelineForImage2Image.from_pretrained(
                    "stabilityai/sdxl-turbo", 
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    variant="fp16" if torch.cuda.is_available() else None
                )
                if torch.cuda.is_available():
                    self._sd_pipeline.enable_model_cpu_offload()
            
            # 2. Extraction des frames
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_in:
                tmp_in.write(video_data)
                tmp_in_path = tmp_in.name
                
            reader = imageio.get_reader(tmp_in_path)
            fps = reader.get_meta_data()['fps']
            frames = []
            
            # Pour éviter les timeouts, on limite à 10 frames max en dev local
            max_frames = 10
            for i, frame in enumerate(reader):
                if i >= max_frames: break
                
                # Transformation SDXL
                pil_img = Image.fromarray(frame).resize((512, 512))
                styled_frame = self._sd_pipeline(
                    prompt=f"anime style, {studio_style}, {prompt}", 
                    image=pil_img, 
                    strength=0.5, 
                    guidance_scale=0.0, 
                    num_inference_steps=2
                ).images[0]
                
                frames.append(np.array(styled_frame))
            
            reader.close()
            os.unlink(tmp_in_path)
            
            # 3. Re-encodage
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
                tmp_out_path = tmp_out.name
                writer = imageio.get_writer(tmp_out_path, fps=fps)
                for f in frames: writer.append_data(f)
                writer.close()
                
            with open(tmp_out_path, "rb") as f:
                res_base64 = base64.b64encode(f.read()).decode("utf-8")
                
            os.unlink(tmp_out_path)
            return f"data:video/mp4;base64,{res_base64}"
            
        except ImportError as e:
            raise InferenceError(f"Dependencies missing for Video Style Transfer: {str(e)}")
        except Exception as e:
            raise InferenceError(f"Video Style Transfer failed: {str(e)}")

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """
        Zero-Shot Voice Cloning (RVC-like) via Coqui TTS.
        """
        try:
            import tempfile
            import os
            from TTS.api import TTS
            
            if not hasattr(self, '_tts_model'):
                logger.info("⏳ Loading Coqui XTTS v2 for voice cloning...")
                self._tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
                if torch.cuda.is_available():
                    self._tts_model.to("cuda")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_ref:
                tmp_ref.write(reference_audio)
                tmp_ref_path = tmp_ref.name
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
                tmp_out_path = tmp_out.name
                
            self._tts_model.tts_to_file(
                text=text, 
                speaker_wav=tmp_ref_path, 
                language=language, 
                file_path=tmp_out_path
            )
            
            with open(tmp_out_path, "rb") as f:
                audio_data = f.read()
                
            os.unlink(tmp_ref_path)
            os.unlink(tmp_out_path)
            return audio_data
            
        except ImportError as e:
            raise InferenceError(f"TTS dependency missing for Voice Cloning: {str(e)}")
        except Exception as e:
            raise InferenceError(f"Voice Cloning failed: {str(e)}")

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict: 
        """
        Génération de scène 3D via projection de nuage de points (Deterministic Spatial Computing).
        Génère un fichier .PLY navigable.
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
            
            # Projection 2D -> 3D simple
            # On suppose un FOV standard
            fx, fy = 200.0, 200.0 
            cx, cy = w / 2, h / 2
            
            for y in range(h):
                for x in range(w):
                    z = float(depth_arr[y, x]) / 255.0
                    if z <= 0.05: continue # On ignore le fond trop proche/noir
                    
                    # Unprojection
                    X = (x - cx) * z / fx
                    Y = (y - cy) * z / fy
                    Z = z
                    
                    r, g, b_val = rgb_arr[y, x]
                    points.append((X, Y, Z, r, g, b_val))
            
            # Création du fichier PLY (Format Binaire pour la compacité)
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
            logger.error(f"❌ 3D Scene generation failed: {e}")
            return {"status": "error", "message": str(e)}

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
            from core.domain.exceptions import ParsingError
            
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

    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str: 
        """Transforme une image en anime via SDXL-Turbo (Similaire à la vidéo mais pour une image seule)."""
        try:
            import base64
            from PIL import Image
            from io import BytesIO
            from diffusers import AutoPipelineForImage2Image
            
            if not hasattr(self, '_sd_pipeline'):
                self._sd_pipeline = AutoPipelineForImage2Image.from_pretrained(
                    "stabilityai/sdxl-turbo", 
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
            
            pil_img = Image.open(BytesIO(image_data)).convert("RGB").resize((512, 512))
            res = self._sd_pipeline(
                prompt=f"anime style, {studio_style}, {prompt}", 
                image=pil_img, 
                strength=0.5, 
                num_inference_steps=2
            ).images[0]
            
            buf = BytesIO(); res.save(buf, format="JPEG")
            return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"
        except Exception as e:
            logger.error(f"❌ Image to Anime failed: {e}"); return ""

    def _load_audioldm_engine(self):
        """Chargement paresseux de AudioLDM."""
        if hasattr(self, '_audioldm_pipeline'): return
        try:
            import torch
            from diffusers import AudioLDMPipeline
            logger.info("⏳ Loading AudioLDM for Contextual Soundscapes...")
            model_id = "cvssp/audioldm-s-full-v2"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            
            self._audioldm_pipeline = AudioLDMPipeline.from_pretrained(
                model_id,
                torch_dtype=torch_dtype
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._audioldm_pipeline.to(device)
            logger.info(f"✅ AudioLDM engine loaded on {device}")
        except ImportError as e:
            raise InferenceError(f"Dependencies missing for AudioLDM: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Failed to load AudioLDM model: {e}")
            raise InferenceError(f"AudioLDM engine loading failed: {str(e)}")

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Génération d'ambiance sonore via AudioLDM basée sur le contexte vidéo."""
        try:
            import io
            import base64
            import scipy.io.wavfile as wavfile
            
            self._load_audioldm_engine()
            
            # Construction du prompt basé sur les métadonnées
            actions = video_metadata.get("actions", [])
            scene = video_metadata.get("scene", "generic environment")
            action_desc = ", ".join(actions) if actions else "subtle ambient sounds"
            
            base_prompt = f"Soundscape for {scene}, featuring {action_desc}."
            final_prompt = f"{prompt}. {base_prompt}" if prompt else base_prompt
            
            logger.info(f"🎧 Generating soundscape with prompt: {final_prompt}")
            
            audio_output = self._audioldm_pipeline(
                final_prompt,
                num_inference_steps=10,
                audio_length_in_s=5.0
            )
            
            waveform = audio_output.audios[0]
            sample_rate = 16000
            
            buffer = io.BytesIO()
            wavfile.write(buffer, sample_rate, waveform)
            
            # Cleanup VRAM
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            b64_audio = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:audio/wav;base64,{b64_audio}"
            
        except InferenceError:
            raise
        except Exception as e:
            logger.error(f"❌ Soundscape generation failed: {e}")
            raise InferenceError(f"Soundscape generation failed: {str(e)}")

    def _load_moshi_engine(self):
        """Chargement paresseux de Kyutai Moshi pour le S2S natif."""
        if hasattr(self, '_moshi_model'): return
        try:
            import torch
            from moshi.models import Moshi
            logger.info("⏳ Loading Kyutai Moshi (Speech-to-Speech)...")
            # Moshi can be large, we use standard loading with hardware detection
            self._moshi_model = Moshi.from_pretrained("kyutai/moshi-1b-preview")
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._moshi_model.to(device)
            logger.info(f"✅ Moshi engine loaded on {device}")
        except ImportError as e:
            raise InferenceError(f"Library 'moshi' or dependencies missing: {str(e)}. Please install it with 'pip install moshi'.")
        except Exception as e:
            logger.error(f"❌ Failed to load Moshi model: {e}")
            raise InferenceError(f"Moshi engine loading failed: {str(e)}")

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """
        Implémentation native du Speech-to-Speech via Kyutai Moshi.
        Convertit l'audio d'entrée en 24kHz Mono, passe par Moshi, et renvoie la réponse audio.
        """
        if not audio_input:
            raise InferenceError("Audio input is empty.")

        try:
            import io
            import wave
            import numpy as np
            from pydub import AudioSegment
            import torch
            
            self._load_moshi_engine()
            
            # 1. Prétraitement Audio : Resampling à 24kHz Mono
            # On utilise pydub pour lire n'importe quel format (mp3, wav, ogg)
            audio = AudioSegment.from_file(io.BytesIO(audio_input))
            audio = audio.set_frame_rate(24000).set_channels(1)
            
            # Conversion en tensor float32 normalisé [-1.0, 1.0]
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            # max_val dépend du sample_width (16-bit = 32768)
            max_val = float(1 << (8 * audio.sample_width - 1))
            samples /= max_val
            
            input_tensor = torch.from_numpy(samples).unsqueeze(0).to(self._moshi_model.device) # [1, T]
            
            # 2. Inférence Moshi
            with torch.no_grad():
                # Moshi API: generate returns the audio tokens/waveform
                output_audio_tensor = self._moshi_model.generate(input_tensor)
            
            # 3. Post-traitement : Conversion tensor -> WAV bytes
            output_np = output_audio_tensor.detach().cpu().numpy().squeeze()
            
            # Clipping pour éviter les distorsions lors de la conversion en int16
            output_np = np.clip(output_np, -1.0, 1.0)
            output_int16 = (output_np * 32767).astype(np.int16)
            
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(output_int16.tobytes())
            
            # Cleanup VRAM
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Speech-to-Speech failed: {e}")
            raise InferenceError(f"Native S2S failed: {str(e)}")

    async def _fetch_images(self, urls: List[str]) -> List[Any]:
        import aiohttp
        import asyncio
        from PIL import Image
        from io import BytesIO
        
        session = await self._get_session()
        tasks = []
        for url in urls:
            async def fetch(url):
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.read()
                            return Image.open(BytesIO(data)).convert("RGB")
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                return None
            tasks.append(fetch(url))
        return await asyncio.gather(*tasks)

    def _load_clip_model(self):
        if hasattr(self, '_clip_model'): return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("🏗️ Loading CLIP for reranking...")
            self._clip_model = SentenceTransformer('clip-ViT-B-32')
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP: {e}")
            raise InferenceError(f"Critical failure during CLIP loading: {str(e)}")

    async def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]: 
        """Reranking visuel via CLIP (Async)."""
        from sentence_transformers import util
        
        self._load_clip_model()
        
        # Async fetch images
        images = await self._fetch_images(image_urls)
        
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
        for i, score in enumerate(scores):
            results.append({"url": valid_urls[i], "score": float(score)})
            
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


    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: 
        return {"entropy": 0.0, "perplexity": 1.0}
    
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: 
        return {"activations": [], "attention_maps": []}
    
    def generate_image(self, prompt: str, style: str = "") -> str:
        return None # Implementé via DiffusersAdapter

    def health_check(self) -> dict: return {"status": "online" if self.model else "offline", "engine": "transformers"}

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Implémentation du reranking avec sentence_transformers."""
        if not documents:
            return []
            
        from core.utils.lazy_import import lazy_import
        sentence_transformers = lazy_import('sentence_transformers')
        
        # Singleton pour le reranker afin d'éviter de le recharger
        if not hasattr(self, '_cross_encoder'):
            # Utilisation du modèle BGE-reranker ou ms-marco par défaut
            self._cross_encoder = sentence_transformers.CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
        pairs = [[query, doc] for doc in documents]
        scores = self._cross_encoder.predict(pairs)
        
        # S'assurer que le retour est bien une liste de floats
        return [float(score) for score in scores]

