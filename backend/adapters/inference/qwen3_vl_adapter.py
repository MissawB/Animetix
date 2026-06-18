import base64
import logging
import os
from typing import List, Dict, Any, Optional
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.ports.usage_port import UsagePort
from core.domain.entities.ai_schemas import InferenceResponse
from huggingface_hub import InferenceClient
from core.utils.model_security import get_verified_revision

logger = logging.getLogger("animetix.inference.qwen3vl")


class Qwen3VLAdapter(InferencePort):
    def __init__(
        self,
        model_id: str = "Qwen/Qwen3-VL-30B-A3B-Instruct",
        token: str = None,
        usage_port: Optional[UsagePort] = None,
    ):
        super().__init__(usage_port=usage_port)
        self.model_id = model_id
        revision = get_verified_revision(self.model_id)

        actual_token = token or os.getenv("HUGGINGFACE_API_KEY")

        # InferenceClient from huggingface_hub does not take a 'revision' param in __init__.
        # We pass it via headers for the Inference API to pin the version if available.
        headers = {}
        if revision:
            headers["X-HuggingFace-Revision"] = revision

        self.client = InferenceClient(
            model=self.model_id, token=actual_token, headers=headers
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ) -> InferenceResponse:
        # Injection de la réflexion si activée
        if thinking_mode:
            thinking_instruction = "\n<think>\nAnalyse la requête en profondeur, explore plusieurs pistes et vérifie tes hypothèses avant de répondre.\n</think>"
            system_prompt = f"{system_prompt}{thinking_instruction}"

        # Le budget peut être utilisé pour max_tokens si supporté par l'endpoint
        max_tokens = 500 + (thinking_budget if thinking_budget > 0 else 0)

        try:
            res = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
            )
            content = res.choices[0].message.content
            self._log_usage(
                engine="qwen3:generate",
                input_tokens=len(prompt) // 4,
                output_tokens=len(content) // 4,
                allocated_budget=thinking_budget,
            )
            return InferenceResponse(text=content)
        except Exception as e:
            logger.error(f"Qwen3-VL generate failed: {e}")
            raise e

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        **kwargs,
    ):
        yield self.generate(
            prompt, system_prompt, thinking_budget, thinking_mode, include_logprobs
        )

    def get_text_embedding(self, text: str) -> List[float]:
        raise InferenceNotImplementedError(
            "Text embedding not supported by Qwen3VLAdapter"
        )

    def localize_video_actions(
        self, video_data: bytes, action_queries: List[str]
    ) -> List[Dict[str, Any]]:
        video_b64 = base64.b64encode(video_data).decode("utf-8")
        results = []
        for query in action_queries:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video",
                            "video": f"data:video/mp4;base64,{video_b64}",
                            "fps": 2.0,
                        },
                        {"type": "text", "text": query},
                    ],
                }
            ]
            try:
                response = self.client.chat_completion(
                    messages=messages, max_tokens=500
                )
                content = response.choices[0].message.content
                self._log_usage(
                    engine="qwen3:video:localize",
                    input_tokens=len(query) // 4 + 512,
                    output_tokens=len(content) // 4,
                )
                results.append({"query": query, "answer": content})
            except Exception as e:
                logger.error(f"Qwen3-VL Video Analysis failed: {e}")
                results.append({"query": query, "answer": f"Error: {e}"})
        return results

    def visual_rerank(
        self,
        query: str,
        image_urls: List[str],
        system_prompt: str = "Tu es un expert en analyse visuelle d'anime.",
    ) -> List[Dict[str, Any]]:
        """Utilise Qwen3-VL pour classer une liste d'images par pertinence visuelle."""
        if not image_urls:
            return []

        # Construction du prompt. Si le query semble déjà être un prompt complexe (contient 'MISSION'), on l'utilise tel quel.
        if "MISSION" in query:
            prompt = query
        else:
            prompt = (
                f"Analyse ces {len(image_urls)} images (indexées de 0 à {len(image_urls) - 1}) et classe-les selon leur pertinence par rapport à la requête : '{query}'.\n"
                'Réponds uniquement sous forme de JSON avec la structure suivante : {"scores": [{"index": 0, "score": 0.95}, ...]}'
            )

        content = [{"type": "text", "text": prompt}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})

        try:
            import json  # noqa: E402
            import re  # noqa: E402

            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                max_tokens=1000,
            )

            text_response = response.choices[0].message.content
            self._log_usage(engine="qwen3:vision:rerank", units=len(image_urls))

            # Extraction JSON robuste
            json_match = re.search(r"\{.*\}", text_response, re.DOTALL)
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
                            final_results.append(
                                {
                                    "index": int(idx),
                                    "score": float(item.get("score", 0.0)),
                                }
                            )

                    if final_results:
                        return final_results
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Qwen3-VL rerank JSON parsing failed: {e}")

            logger.warning(
                "Qwen3-VL rerank returned malformed JSON or incomplete results. Using fallback."
            )
            return [
                {"index": i, "score": 1.0 / len(image_urls)}
                for i in range(len(image_urls))
            ]

        except Exception as e:
            logger.error(f"Qwen3-VL visual rerank failed: {e}")
            return [{"index": i, "score": 0.0} for i in range(len(image_urls))]

    def health_check(self) -> dict:
        return {"status": "online", "engine": "Qwen3-VL"}
