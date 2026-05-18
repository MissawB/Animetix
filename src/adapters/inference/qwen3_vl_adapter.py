import base64
import logging
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort
from huggingface_hub import InferenceClient

logger = logging.getLogger("animetix.inference.qwen3vl")

class Qwen3VLAdapter(InferencePort):
    def __init__(self, model_id: str = "Qwen/Qwen3-VL-30B-A3B-Instruct", token: str = None):
        self.client = InferenceClient(model=model_id, token=token)

    def localize_video_actions(self, video_data: bytes, action_queries: List[str]) -> List[Dict[str, Any]]:
        video_b64 = base64.b64encode(video_data).decode("utf-8")
        results = []
        for query in action_queries:
            messages = [{
                "role": "user",
                "content": [
                    {"type": "video", "video": f"data:video/mp4;base64,{video_b64}", "fps": 2.0},
                    {"type": "text", "text": query}
                ]
            }]
            try:
                response = self.client.chat_completion(messages=messages, max_tokens=500)
                results.append({"query": query, "answer": response.choices[0].message.content})
            except Exception as e:
                logger.error(f"Qwen3-VL Video Analysis failed: {e}")
                results.append({"query": query, "answer": f"Error: {e}"})
        return results

    # Required Port methods (minimal implementation for now)
    def generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False) -> str:
        # Injection de la réflexion si activée
        if thinking_mode:
            thinking_instruction = "\n<think>\nAnalyse la requête en profondeur, explore plusieurs pistes et vérifie tes hypothèses avant de répondre.\n</think>"
            system_prompt = f"{system_prompt}{thinking_instruction}"

        # Le budget peut être utilisé pour max_tokens si supporté par l'endpoint
        max_tokens = 500 + (thinking_budget if thinking_budget > 0 else 0)
        
        res = self.client.chat_completion(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return res.choices[0].message.content

    def stream_generate(self, prompt: str, system_prompt: str = "", thinking_budget: int = 0, thinking_mode: bool = False):
        yield self.generate(prompt, system_prompt, thinking_budget, thinking_mode)

    def calculate_visual_similarity(self, query: str, item_id: str, media_type: str) -> float: 
        raise NotImplementedError("calculate_visual_similarity not implemented for Qwen3-VL")
        
    def get_image_embedding(self, image_data: bytes, model_id: Optional[str] = None) -> List[float]: 
        raise NotImplementedError("get_image_embedding not implemented for Qwen3-VL")
        
    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]: 
        raise NotImplementedError("classify_image not implemented for Qwen3-VL")
        
    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]: 
        raise NotImplementedError("detect_objects not implemented for Qwen3-VL")
        
    def get_video_temporal_embeddings(self, video_data: bytes) -> List[Dict[str, Any]]: 
        raise NotImplementedError("get_video_temporal_embeddings not implemented for Qwen3-VL")
        
    def transform_image_to_anime(self, image_data: bytes, studio_style: str, prompt: str = "") -> str: 
        raise NotImplementedError("transform_image_to_anime not implemented for Qwen3-VL")
    def transform_video_to_anime(self, video_data: bytes, studio_style: str, prompt: str = "") -> str: return ""
    def generate_soundscape(self, video_metadata: Dict[str, Any], prompt: Optional[str] = None) -> str: return ""
    def clone_voice(self, text: str, reference_audio: bytes, language: str = "fr") -> bytes: return b""
    def speech_to_speech(self, audio_input: bytes, system_prompt: str = "") -> bytes: return b""
    def process_manga_page(self, image_data: bytes) -> Dict[str, Any]: return {}
    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]: return {}
    def inpaint_text_bubbles(self, image_data: bytes, text_placements: List[Dict]) -> str: return ""
    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]: return {"is_safe": True}
    def generate_image_description(self, image_data: bytes, prompt: str = "") -> str: return ""
    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]: return {}
    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]: return {}
    def estimate_depth(self, image_data: bytes) -> bytes: return b""
    def generate_3d_scene(self, image_data: bytes, depth_map: bytes) -> Dict[str, Any]: return {}
    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "Tu es un expert en analyse visuelle d'anime.") -> List[Dict[str, Any]]:
        """Utilise Qwen3-VL pour classer une liste d'images par pertinence visuelle."""
        if not image_urls:
            return []

        prompt = f"Analyse ces {len(image_urls)} images et classe-les selon leur pertinence par rapport à la requête : '{query}'.\n" \
                 "Réponds uniquement sous forme de JSON avec la structure suivante : {\"results\": [{\"url\": \"...\", \"score\": 0.95}, ...]}"

        content = [{"type": "text", "text": prompt}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})

        try:
            import json
            import re
            
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000
            )
            
            text_response = response.choices[0].message.content
            
            # Extract JSON from text response
            json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    results = data.get("results", [])
                    
                    if results and len(results) == len(image_urls):
                        return results
                except json.JSONDecodeError:
                    pass
            
            logger.warning("Qwen3-VL rerank returned malformed JSON or incomplete results. Using fallback.")
            return [{"url": url, "score": 1.0 / len(image_urls)} for url in image_urls]
            
        except Exception as e:
            logger.error(f"Qwen3-VL visual rerank failed: {e}")
            return [{"url": url, "score": 0.0} for url in image_urls]

    def get_multimodal_late_interaction(self, image_data: bytes) -> List[List[float]]: return []
    def health_check(self) -> dict: return {"status": "online", "engine": "Qwen3-VL"}
