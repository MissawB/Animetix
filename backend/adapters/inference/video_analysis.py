"""Video analysis mixin for VisionTransformersAdapter."""
import logging
from typing import List, Dict, Any
from core.utils.lazy_import import lazy_import
from core.domain.exceptions import InferenceError

torch = lazy_import('torch')
transformers = lazy_import('transformers')

logger = logging.getLogger("animetix.inference.video_analysis")


class VideoAnalysisMixin:
    """Provides video temporal analysis, action localization, and description."""

    def _load_video_vlm(self):
        """Chargement paresseux de Qwen2-VL pour le RAG temporel."""
        if hasattr(self, '_video_vlm'):
            return
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
            import torch as _torch

            logger.info("📽️ Loading Qwen2-VL-2B for Temporal RAG...")
            model_id = "Qwen/Qwen2-VL-2B-Instruct"

            quantization_config = None
            if self.use_4bit:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=_torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )

            self._video_processor = AutoProcessor.from_pretrained(model_id)
            self._video_vlm = Qwen2VLForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=_torch.float16 if _torch.cuda.is_available() else _torch.float32,
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

            total_frames = int(duration * fps)
            indices = [int(i * total_frames / max_frames) for i in range(max_frames)]

            frames = []
            for i, frame in enumerate(reader):
                if i in indices:
                    frames.append(Image.fromarray(frame).convert("RGB"))
                if len(frames) >= max_frames:
                    break

            reader.close()
            os.unlink(tmp_path)
            return frames
        except Exception as e:
            logger.error(f"❌ Frame sampling failed: {e}")
            return []

    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]:
        """Analyse temporelle profonde via Qwen2-VL."""
        try:
            self._load_video_vlm()
            frames = self._sample_video_frames(video_data, max_frames=8)
            if not frames:
                return []

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "video", "video": frames, "fps": 1.0},
                        {"type": "text", "text": "Describe the main actions and key moments in this video segment with timestamps."}
                    ]
                }
            ]

            import torch as _torch
            text = self._video_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self._video_processor(text=[text], videos=[frames], padding=True, return_tensors="pt").to(self._video_vlm.device)

            generated_ids = self._video_vlm.generate(**inputs, max_new_tokens=256)
            output_text = self._video_processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

            self._log_usage(engine="transformers:Qwen2-VL-2B:temporal", units=1)

            return [{"start": 0, "end": -1, "summary": output_text, "confidence": 0.9}]

        except Exception as e:
            logger.error(f"❌ Video temporal analysis failed: {e}")
            raise InferenceError(f"Video reasoning failed: {str(e)}")

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        """Localise des actions spécifiques dans une vidéo via raisonnement par fenêtre glissante."""
        try:
            self._load_video_vlm()
            import orjson

            frames = self._sample_video_frames(video_data, max_frames=8)
            if not frames:
                return []

            all_found_actions = []

            for query in action_queries:
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

                self._log_usage(engine="transformers:Qwen2-VL-2B:localize", units=1)

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

    def generate_video_description(self, video_data: bytes, prompt: str = "Décris cette vidéo d'anime.") -> str:
        """Utilise Qwen2-VL pour décrire une vidéo."""
        try:
            self._load_video_vlm()
            frames = self._sample_video_frames(video_data, max_frames=8)
            if not frames:
                return "Aucune frame extraite."

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

            generated_ids = self._video_vlm.generate(**inputs, max_new_tokens=512)
            output_text = self._video_processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

            self._log_usage(engine="transformers:Qwen2-VL:video_description", units=1)

            return output_text
        except Exception as e:
            logger.error(f"❌ Video description failed: {e}")
            return f"Erreur Video-LLaVA: {e}"
