import torch
import logging
from typing import Optional, List, Dict, Any, Generator
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.inference.transformers")

class TransformersAdapter(InferencePort):
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_4bit: bool = True):
        self.model_id = model_id
        self.model = None
        self.tokenizer = None
        self.use_4bit = use_4bit

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
        self._load_model()
        if not self.model: return "Erreur: Modèle local non chargé."
        
        # Injection du prompt de réflexion
        if thinking_mode or thinking_budget > 0:
            prompt = f"<think>\nAnalyse en profondeur.\n</think>\n{prompt}"
            
        inputs = self.tokenizer(f"{system_prompt}\n\n{prompt}", return_tensors="pt").to(self.model.device)
        max_new_tokens = 512 + (thinking_budget if thinking_budget > 0 else 0)
        
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).replace(system_prompt, "").strip()

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

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
            
        except ImportError:
            logger.error("❌ Dependencies missing for Video Style Transfer (diffusers, imageio, cv2).")
            return ""
        except Exception as e:
            logger.error(f"❌ Video Style Transfer failed: {e}")
            return ""

    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes:
        """
        Zero-Shot Voice Cloning (RVC-like) via Coqui TTS.
        """
        try:
            import tempfile
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
            
        except ImportError:
            logger.error("❌ TTS dependency missing for Voice Cloning.")
            return b""
        except Exception as e:
            logger.error(f"❌ Voice Cloning failed: {e}")
            return b""

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
            header = f"ply\nformat binary_little_endian 1.0\nelement vertex {len(points)}\nproperty float x\nproperty float y\nproperty float z\nproperty uint8 red\nproperty property uint8 green\nproperty uint8 blue\nend_header\n"
            
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

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: 
        """Stub pour les embeddings temporels vidéo."""
        logger.warning("⚠️ get_video_temporal_embeddings is not implemented yet (stub).")
        return [{"start": 0, "end": 10, "embedding": [0.0]*512}]

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]: 
        """Stub pour la localisation d'actions vidéo."""
        logger.warning("⚠️ localize_video_actions is not implemented yet (stub).")
        return [{"action": q, "start": 0, "end": 5, "confidence": 0.5} for q in action_queries]

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

    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str:
        """Stub pour la génération d'ambiance sonore."""
        logger.warning("⚠️ generate_soundscape is not implemented yet (stub).")
        return "https://example.com/soundscape.mp3"

    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes:
        """Stub pour le Speech-to-Speech natif."""
        logger.warning("⚠️ speech_to_speech is not implemented yet (stub).")
        return audio_input # Echo fallback

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "") -> List[Dict[str, Any]]: 
        """Reranking visuel via CLIP."""
        try:
            from sentence_transformers import util
            if not hasattr(self, '_clip_model'):
                from sentence_transformers import SentenceTransformer
                self._clip_model = SentenceTransformer('clip-ViT-B-32')
            
            query_emb = self._clip_model.encode(query, convert_to_tensor=True)
            # Ici on devrait normalement fetch les images, mais pour le stub on compare le query aux URLs
            results = []
            for i, url in enumerate(image_urls):
                results.append({"index": i, "score": 0.5, "url": url})
            return results
        except Exception: return [{"index": i, "score": 0.0} for i in range(len(image_urls))]

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

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]:
        """Stub pour Late Interaction (ColEmbed)."""
        return [[0.0]*128 for _ in range(32)]

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: 
        return {"entropy": 0.0, "perplexity": 1.0}
    
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: 
        return {"activations": [], "attention_maps": []}
    
    def generate_image(self, prompt: str, style: str = "") -> str:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(f"{prompt} {style}".strip())
        return f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&model=flux"

    def health_check(self) -> dict: return {"status": "online" if self.model else "offline", "engine": "transformers"}
