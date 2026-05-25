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

    def visual_rerank(self, query: str, image_urls: List[str], system_prompt: str = "Tu es un expert en analyse visuelle d'anime.") -> List[Dict[str, Any]]:
        """Utilise Qwen3-VL pour classer une liste d'images par pertinence visuelle."""
        if not image_urls:
            return []

        # Construction du prompt. Si le query semble déjà être un prompt complexe (contient 'MISSION'), on l'utilise tel quel.
        if "MISSION" in query:
            prompt = query
        else:
            prompt = f"Analyse ces {len(image_urls)} images (indexées de 0 à {len(image_urls)-1}) et classe-les selon leur pertinence par rapport à la requête : '{query}'.\n" \
                     "Réponds uniquement sous forme de JSON avec la structure suivante : {\"scores\": [{\"index\": 0, \"score\": 0.95}, ...]}"

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
            
            # Extraction JSON robuste
            json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    results = data.get("scores") or data.get("results") or []
                    
                    final_results = []
                    for i, item in enumerate(results):
                        idx = item.get("index")
                        if idx is None and "url" in item:
                            try:
                                idx = image_urls.index(item["url"])
                            except ValueError:
                                idx = i
                        
                        if idx is not None:
                            final_results.append({
                                "index": int(idx),
                                "score": float(item.get("score", 0.0))
                            })
                    
                    if final_results:
                        return final_results
                except (json.JSONDecodeError, ValueError):
                    pass
            
            logger.warning("Qwen3-VL rerank returned malformed JSON or incomplete results. Using fallback.")
            return [{"index": i, "score": 1.0 / len(image_urls)} for i in range(len(image_urls))]
            
        except Exception as e:
            logger.error(f"Qwen3-VL visual rerank failed: {e}")
            return [{"index": i, "score": 0.0} for i in range(len(image_urls))]

    def health_check(self) -> dict: return {"status": "online", "engine": "Qwen3-VL"}

