import os
import httpx
import json
import re
import time
import logging
import base64
import functools
from typing import Optional, List, Dict, Any
from core.ports.inference_port import InferencePort, InferenceNotImplementedError
from core.utils.security import is_safe_url, safe_http_request
from core.domain.exceptions import InferenceError
from core.domain.entities.ai_schemas import InferenceResponse, InferenceMetadata, TokenLogProb

# Focused Mixin imports
from adapters.inference.clip_vision import ClipVisionMixin
from adapters.inference.depth_estimation import DepthEstimationMixin
from adapters.inference.manga_ocr import MangaOcrMixin
from adapters.inference.video_analysis import VideoAnalysisMixin
from adapters.inference.audio_mixin import AudioMixin
from adapters.inference.image_gen_mixin import ImageGenMixin
from adapters.inference.vlm_mixin import VlmMixin
from adapters.inference.rerank_mixin import RerankMixin

logger = logging.getLogger("animetix." + __name__)

@functools.lru_cache(maxsize=1)
def _get_evaluation_resources():
    """Charge de manière paresseuse et met en cache le modèle d'évaluation pour les diagnostics."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    model_id = "gpt2"
    logger.info(f"Loading evaluation model {model_id} for observability...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, output_attentions=True, output_hidden_states=True)
    model.eval()
    return model, tokenizer, torch

class UnifiedInferenceAdapter(
    ClipVisionMixin,
    DepthEstimationMixin,
    MangaOcrMixin,
    VideoAnalysisMixin,
    AudioMixin,
    ImageGenMixin,
    VlmMixin,
    RerankMixin,
    InferencePort
):
    """
    Unified Inference Adapter supporting local Ollama and OpenAI-compatible endpoints.
    Composes specialized mixins for vision, audio, and image generation as local fallbacks.
    """
    def __init__(
        self,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 90,
        usage_port: Optional[Any] = None
    ):
        super().__init__(usage_port=usage_port)
        # Default to local Ollama OpenAI-compatible endpoint
        self.api_base = api_base or os.getenv("LLM_API_BASE") or "http://localhost:11434/v1"
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME") or "llama3"
        self.api_key = api_key or os.getenv("LLM_API_KEY") or "ollama"
        self.max_retries = max_retries
        self.timeout = timeout

        if not is_safe_url(self.api_base, allow_internal=True):
            logger.warning(f"UnifiedInferenceAdapter: API base URL might be unsafe: {self.api_base}")

        logger.info(f"Initialized UnifiedInferenceAdapter for {self.model_name} at {self.api_base}")

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def get_text_embedding(self, text: str) -> List[float]:
        """Génère un embedding vectoriel pour un texte donné."""
        try:
            url = f"{self.api_base}/embeddings"
            payload = {
                "model": self.model_name,
                "input": text
            }
            # Utilisation de safe_http_request avec allow_internal=True car api_base est configuré
            res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)
            if res.status_code == 200:
                data = res.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                elif "embedding" in data:
                    return data["embedding"]
            
            # Fallback to direct Ollama api
            direct_url = f"{self.api_base.replace('/v1', '')}/api/embeddings"
            direct_payload = {
                "model": self.model_name,
                "prompt": text
            }
            res = safe_http_request("POST", direct_url, json=direct_payload, timeout=self.timeout, allow_internal=True)
            if res.status_code == 200:
                return res.json().get("embedding", [])
            
            res.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to generate text embedding via UnifiedInferenceAdapter: {e}")
            raise InferenceError(f"Embedding generation failed: {e}")
        return []

    def generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False,
        json_mode: bool = False
    ) -> InferenceResponse:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2 if json_mode else 0.7
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {
                "thinking_budget": thinking_budget,
                "thinking_mode": thinking_mode
            }

        if include_logprobs:
            payload["logprobs"] = True
            payload["top_logprobs"] = 5

        last_error = None
        for attempt in range(self.max_retries):
            try:
                url = f"{self.api_base}/chat/completions"
                res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)

                if res.status_code == 400 and "extra_body" in payload:
                    logger.warning("Target LLM server rejected thinking parameters, retrying without them.")
                    del payload["extra_body"]
                    res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)
                
                if res.status_code == 400 and json_mode:
                    logger.warning("Target LLM server rejected JSON mode, retrying with raw text.")
                    del payload["response_format"]
                    res = safe_http_request("POST", url, json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)

                res.raise_for_status()
                data = res.json()

                usage = data.get("usage", {})
                self._log_usage(
                    engine=f"unified:{self.model_name}",
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0)
                )

                if isinstance(data, dict) and "choices" in data:
                    choice = data["choices"][0]
                    raw_content = choice["message"]["content"]
                    
                    # Extraction des logprobs si présentes
                    parsed_logprobs = None
                    if "logprobs" in choice and choice["logprobs"] and "content" in choice["logprobs"]:
                        parsed_logprobs = []
                        for lp in choice["logprobs"]["content"]:
                            top_lp = None
                            if "top_logprobs" in lp and lp["top_logprobs"]:
                                # Conversion vers List[Dict[str, float]] attendue par le schéma
                                top_lp = [{item["token"]: item["logprob"]} for item in lp["top_logprobs"]]
                            
                            parsed_logprobs.append(TokenLogProb(
                                token=lp["token"],
                                logprob=lp["logprob"],
                                top_logprobs=top_lp
                            ))
                else:
                    raw_content = str(data)
                    parsed_logprobs = None

                if "---" in raw_content:
                    raw_content = raw_content.split("---")[0].strip()

                return InferenceResponse(
                    text=raw_content,
                    metadata=InferenceMetadata(
                        logprobs=parsed_logprobs,
                        usage=usage
                    )
                )
            except httpx.RequestError as e:
                last_error = e
                logger.error(f"Inference attempt {attempt+1}/{self.max_retries} failed: {e}")
                time.sleep(1)
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error in UnifiedInferenceAdapter: {e}")
                break

        raise InferenceError(f"Le service d'inférence ({self.model_name}) est indisponible. Dernier essai: {last_error}")

    def generate_structured(self, prompt: str, response_model: Any, system_prompt: str = "", max_retries: int = 3) -> Any:
        # Tente d'utiliser instructor pour une vraie génération structurée
        try:
            import instructor
            from openai import OpenAI
            import pydantic
            
            # Uniquement si on a un modèle pydantic valide
            if isinstance(response_model, type) and issubclass(response_model, pydantic.BaseModel):
                client = instructor.from_openai(
                    OpenAI(base_url=self.api_base, api_key=self.api_key),
                    mode=instructor.Mode.JSON
                )
                
                self._log_usage(engine=f"unified:{self.model_name}:structured", units=1)
                
                return client.chat.completions.create(
                    model=self.model_name,
                    response_model=response_model,
                    messages=[
                        {"role": "system", "content": system_prompt or "Tu es un expert en extraction de données structurées."},
                        {"role": "user", "content": prompt}
                    ],
                    max_retries=max_retries
                )
        except ImportError:
            logger.debug("Instructor ou OpenAI manquant, fallback vers le parsing JSON manuel.")
        except Exception as e:
            logger.warning(f"Echec instructor: {e}. Fallback vers le parsing JSON manuel.")

        # Fallback classique (Regex)
        try:
            response = self.generate(prompt, system_prompt=system_prompt, json_mode=True)
            clean_json = response.text.strip()
            if "```" in clean_json:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_json, re.DOTALL | re.IGNORECASE)
                if match:
                    clean_json = match.group(1)
                else:
                    start = clean_json.find('{')
                    end = clean_json.rfind('}')
                    if start != -1 and end != -1:
                        clean_json = clean_json[start:end+1]

            data = json.loads(clean_json)
            if hasattr(response_model, "model_validate"):
                return response_model.model_validate(data)
            return data
        except Exception as e:
            logger.error(f"Failed structured generation in UnifiedInferenceAdapter: {e}")
            raise InferenceError(f"Structured generation failed: {e}")


    def stream_generate(
        self,
        prompt: str,
        system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
        thinking_budget: int = 0,
        thinking_mode: bool = False,
        include_logprobs: bool = False
    ):
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "stream": True
        }

        if thinking_mode or thinking_budget > 0:
            payload["extra_body"] = {
                "thinking_budget": thinking_budget,
                "thinking_mode": thinking_mode
            }

        if include_logprobs:
            payload["logprobs"] = True
            payload["top_logprobs"] = 5

        url = f"{self.api_base}/chat/completions"
        try:
            # Sécurité SSRF: On valide l'URL avant le stream
            if not is_safe_url(url, allow_internal=True):
                 raise ValueError(f"Unsafe stream URL: {url}")

            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                with client.stream("POST", url, json=payload, headers=self._get_headers()) as res:
                    if res.status_code == 400 and "extra_body" in payload:
                        logger.warning("Target LLM server rejected thinking parameters for streaming, retrying without.")
                        # Retrying in a stream is complex, here we just return the error for now or would need to restart the loop
                        pass

                    res.raise_for_status()
                    for line in res.iter_lines():
                        if line:
                            if line.startswith("data: "):
                                data_content = line[6:].strip()
                                if data_content == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_content)
                                    choice = chunk['choices'][0]
                                    delta = choice.get('delta', {})
                                    
                                    # Extraction des logprobs par token si présentes dans le chunk
                                    parsed_logprobs = None
                                    if "logprobs" in choice and choice["logprobs"] and "content" in choice["logprobs"]:
                                        parsed_logprobs = []
                                        for lp in choice["logprobs"]["content"]:
                                            top_lp = None
                                            if "top_logprobs" in lp and lp["top_logprobs"]:
                                                # Conversion vers List[Dict[str, float]] attendue par le schéma
                                                top_lp = [{item["token"]: item["logprob"]} for item in lp["top_logprobs"]]

                                            parsed_logprobs.append(TokenLogProb(
                                                token=lp["token"],
                                                logprob=lp["logprob"],
                                                top_logprobs=top_lp
                                            ))

                                    if 'content' in delta:
                                        yield InferenceResponse(
                                            text=delta['content'],
                                            metadata=InferenceMetadata(
                                                logprobs=parsed_logprobs,
                                                usage=chunk.get("usage")
                                            )
                                        )
                                except Exception as e:
                                    logger.warning(f"Error parsing stream chunk: {e}")
                                    continue
        except Exception as e:
            logger.error(f"Unified Stream Error: {e}")
            raise InferenceError(f"Streaming failed: {e}")

    def rerank_documents(self, query: str, documents: List[str]) -> List[float]:
        """Ré-ordonne les documents via un prompt LLM (fallback)."""
        if not documents:
            return []

        prompt = f"Requête: {query}\n\nDocuments à évaluer:\n"
        for i, doc in enumerate(documents):
            prompt += f"ID {i}: {doc[:500]}\n"

        prompt += "\nPour chaque document, donne un score de pertinence entre 0.0 (inutile) et 1.0 (parfait). Réponds avec une liste de scores JSON: [score0, score1, ...]"

        try:
            response = self.generate(prompt, system_prompt="Tu es un système de réordonnancement (reranker) expert.", json_mode=False)
            raw = response.text
            match = re.search(r'\[.*\]', raw)
            if match:
                scores = json.loads(match.group(0))
                if len(scores) == len(documents):
                    return [float(s) for s in scores]
        except Exception as e:
            logger.warning(f"Reranking fallback failed: {e}")

        return [0.0] * len(documents)

    def moderate_content(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Modère le contenu via un prompt LLM."""
        prompt = f"Texte à analyser: {text}\n\nCatégories à vérifier: {', '.join(categories)}\n\nRéponds au format JSON: {{'is_safe': bool, 'flagged_categories': [str], 'reason': str}}"
        try:
            return self.generate_structured(prompt, response_model=dict, system_prompt="Tu es un agent de modération.")
        except Exception:
            return {"is_safe": True, "flagged_categories": [], "reason": "Moderation fallback failed."}

    def classify_image(self, image_data: bytes, candidate_labels: List[str], model_id: Optional[str] = None) -> Dict[str, float]:
        """Classifie une image via VLM prompt avec fallback sur CLIP."""
        prompt = f"Parmi ces labels: {', '.join(candidate_labels)}, lequel correspond le mieux à cette image ? Réponds au format JSON: {{'label': score}}."
        try:
            desc = self.generate_image_description(image_data, prompt=prompt)
            match = re.search(r'\{.*\}', desc, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Classification VLM failed: {e}. Falling back to CLIP.")
        
        # Delegation to ClipVisionMixin if available
        if hasattr(super(), 'classify_image'):
            return super().classify_image(image_data, candidate_labels, model_id)
        return {l: 0.0 for l in candidate_labels}

    def detect_objects(self, image_data: bytes, candidate_queries: List[str], model_id: Optional[str] = None) -> List[Dict]:
        """Détecte des objets via VLM prompt avec fallback sur OwlViT."""
        prompt = f"Détecte ces éléments dans l'image: {', '.join(candidate_queries)}. Réponds au format JSON: [{{'label': str, 'box_2d': [ymin, xmin, ymax, xmax], 'score': float}}]."
        try:
            desc = self.generate_image_description(image_data, prompt=prompt)
            match = re.search(r'\[.*\]', desc, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Object detection VLM failed: {e}. Falling back to specialized model.")
        
        # Delegation to VlmMixin
        if hasattr(super(), 'detect_objects'):
            return super().detect_objects(image_data, candidate_queries, model_id)
        return []

    def generate_image_description(self, image_data: bytes, prompt: str = "Décris cette image d'anime de manière très détaillée.") -> str:
        """Utilise un VLM si le endpoint d'inférence supporte les requêtes multimodales. Fallback sur Moondream2."""
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            payload = {
                "model": self.model_name,
                "messages": [
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
            }
            res = safe_http_request("POST", f"{self.api_base}/chat/completions", json=payload, headers=self._get_headers(), timeout=self.timeout, allow_internal=True)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Unified multimodal description failed: {e}. Falling back to local VLM.")

        # Delegation to VlmMixin
        if hasattr(super(), 'generate_image_description'):
            return super().generate_image_description(image_data, prompt)
        
        raise InferenceError(f"Multimodal description failed and no fallback available.")

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> Dict[str, Any]:
        """Détecte, OCR, traduit et redessine le texte dans les bulles d'une page de manga."""
        try:
            # 1. OCR
            ocr_res = self.process_manga_page(image_data)
            if ocr_res["status"] != "success":
                raise InferenceError("OCR failed during manga translation.")
            
            layout = ocr_res["layout"]
            
            # 2. Translation
            for entry in layout:
                orig_text = entry.get("text", "")
                if orig_text:
                    prompt = f"Traduis ce texte de manga en {target_lang}: {orig_text}. Réponds UNIQUEMENT avec le texte traduit."
                    response = self.generate(prompt, system_prompt="Tu es un traducteur expert de manga.")
                    entry["text"] = response.text

            
            # 3. Inpainting (Redessiner)
            text_placements = [{"bbox": e.get("box", e.get("bbox")), "text": e["text"]} for e in layout]
            final_image_url = self.inpaint_text_bubbles(image_data, text_placements)
            
            return {
                "translated_image": final_image_url,
                "layout": layout,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Translate manga page failed: {e}")
            raise InferenceError(f"Manga translation failed: {e}")

    def get_diagnostics(self, prompt: str, completion: str) -> Dict[str, Any]:
        """Récupère les données d'activation internes réelles (Logit Lens, Attention) via un modèle d'évaluation."""
        try:
            model, tokenizer, torch = _get_evaluation_resources()

            text = completion if len(completion.strip()) > 0 else " "
            inputs = tokenizer(text, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model(**inputs)
            
            # 1. Attention Map
            # outputs.attentions is a tuple of (batch, num_heads, seq_len, seq_len)
            # We take the last layer, mean across all heads
            if outputs.attentions:
                last_layer_attention = outputs.attentions[-1][0].mean(dim=0) # (seq_len, seq_len)
                # Take up to 10 tokens to avoid massive JSON
                seq_len = min(last_layer_attention.size(0), 10)
                attention_map = last_layer_attention[:seq_len, :seq_len].tolist()
                
                # Format to 4 decimals
                attention_map = [[round(val, 4) for val in row] for row in attention_map]
            else:
                attention_map = []

            # 2. Logit Lens
            # outputs.hidden_states is a tuple of (batch, seq_len, hidden_size)
            # We project each hidden state to vocabulary using model.lm_head
            logit_projections = []
            if outputs.hidden_states:
                # Select a few representative layers
                total_layers = len(outputs.hidden_states)
                layers_to_check = [0, total_layers // 2, total_layers - 1]
                layer_names = ["Embeddings", "Middle_Layer", "Output_Layer"]
                
                for idx, layer_idx in enumerate(layers_to_check):
                    hidden_state = outputs.hidden_states[layer_idx][0, -1, :] # Last token
                    # Project to vocab
                    if hasattr(model, 'lm_head'):
                        logits = model.lm_head(hidden_state)
                    else:
                        # Fallback for models without direct lm_head
                        logits = torch.nn.functional.linear(hidden_state, model.get_input_embeddings().weight)
                        
                    probs = torch.nn.functional.softmax(logits, dim=-1)
                    
                    top_prob, top_token_id = torch.max(probs, dim=-1)
                    top_token = tokenizer.decode([top_token_id.item()])
                    
                    logit_projections.append({
                        "layer": f"Layer_{layer_idx} ({layer_names[idx]})",
                        "top_token": top_token.strip() or "[SPACE]",
                        "confidence": round(top_prob.item(), 4)
                    })

            return {
                "attention_map": attention_map,
                "logit_lens": logit_projections,
                "runtime_ms": 0.0,
                "model_signature": "evaluation_model:gpt2:observability"
            }
        except Exception as e:
            logger.error(f"Error in real get_diagnostics: {e}")
            raise InferenceError(f"Failed to get diagnostics: {e}")

    def calculate_uncertainty(self, prompt: str, completion: str) -> Dict[str, float]:
        """Calcule la certitude mathématique réelle (entropie, perplexité) d'une génération via un modèle local."""
        try:
            model, tokenizer, torch = _get_evaluation_resources()

            text = prompt + "\n" + completion
            inputs = tokenizer(text, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model(**inputs, labels=inputs["input_ids"])
                loss = outputs.loss
                logits = outputs.logits
            
            # Perplexity is exp(loss)
            perplexity = torch.exp(loss).item()
            
            # Entropy calculation over the vocabulary for the generated tokens
            probs = torch.nn.functional.softmax(logits, dim=-1)
            log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
            entropy = -(probs * log_probs).sum(dim=-1).mean().item()
            
            # Confidence is inversely proportional to normalized entropy
            # max entropy for GPT-2 vocab (50257) is ln(50257) ~= 10.8
            confidence = max(0.0, min(1.0, 1.0 - (entropy / 10.8)))

            return {
                "entropy": round(entropy, 4),
                "perplexity": round(perplexity, 4),
                "confidence": round(confidence, 4)
            }
        except Exception as e:
            logger.error(f"Error calculating real uncertainty: {e}")
            raise InferenceError(f"Failed to calculate uncertainty: {e}")

    def health_check(self) -> dict:
        try:
            res = safe_http_request("GET", f"{self.api_base.replace('/v1', '')}/api/tags", timeout=5, allow_internal=True)
            if res.status_code == 200:
                return {"status": "online", "engine": "Ollama/Unified", "models": res.json().get("models", [])}
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")

        try:
            res = safe_http_request("GET", f"{self.api_base}/models", headers=self._get_headers(), timeout=5, allow_internal=True)
            if res.status_code == 200:
                return {"status": "online", "engine": "OpenAI-Compatible/Unified"}
        except Exception as e:
            logger.debug(f"OpenAI-Compatible health check failed: {e}")

        return {"status": "offline", "engine": "Unified"}

    def generate_3d_scene(self, image_data: bytes, depth_map: bytes = None, mode: str = "gaussian_splatting") -> Dict[str, Any]:
        """Génère un espace 3D navigable (Gaussian Splatting / Mesh) à partir d'une image via Tripo3D API."""
        try:
            import base64
            
            logger.info(f"Initializing 3D Generation ({mode})...")
            tripo_api_key = os.getenv("TRIPO_API_KEY")
            
            if not tripo_api_key:
                logger.warning("TRIPO_API_KEY non configurée. Fallback sur le mock de génération 3D.")
                # Simulation réaliste du retour d'une API 3D (ex: Luma AI ou CSM)
                mock_3d_generation_result = {
                    "status": "success",
                    "task_id": "3d_gen_8f92a1b",
                    "mode": mode,
                    "model_url": "https://cdn.animetix.ai/3d-models/generated_splat_demo.glb",
                    "preview_video": "https://cdn.animetix.ai/3d-models/previews/demo.mp4",
                    "polycount": 250000,
                    "format": "GLB",
                    "metadata": {
                        "source_resolution": "1024x1024",
                        "depth_guided": depth_map is not None,
                        "engine": "Mock-Splatting"
                    }
                }
                
                self._log_usage(engine="cloud:mock_3d", units=1)
                return mock_3d_generation_result
                
            headers = {
                "Authorization": f"Bearer {tripo_api_key}"
            }
            
            # Étape 1 : Uploader l'image
            upload_url = "https://api.tripo3d.ai/v2/openapi/upload"
            files = {
                "file": ("image.jpg", image_data, "image/jpeg")
            }
            
            logger.info("Uploading image to Tripo3D...")
            with httpx.Client(timeout=30) as client:
                upload_res = client.post(upload_url, headers=headers, files=files)
                upload_res.raise_for_status()
                file_token = upload_res.json()["data"]["image_token"]
            
            # Étape 2 : Créer la tâche de génération
            task_url = "https://api.tripo3d.ai/v2/openapi/task"
            task_payload = {
                "type": "image_to_model",
                "file": {
                    "type": "jpg",
                    "file_token": file_token
                }
            }
            
            logger.info("Creating Tripo3D task...")
            with httpx.Client(timeout=30) as client:
                task_res = client.post(task_url, headers={"Authorization": f"Bearer {tripo_api_key}", "Content-Type": "application/json"}, json=task_payload)
                task_res.raise_for_status()
                task_id = task_res.json()["data"]["task_id"]
            
            # Étape 3 : Polling du résultat
            logger.info(f"Polling Tripo3D task: {task_id}...")
            max_attempts = 60
            attempt = 0
            model_url = None
            
            while attempt < max_attempts:
                with httpx.Client(timeout=10) as client:
                    status_res = client.get(f"https://api.tripo3d.ai/v2/openapi/task/{task_id}", headers=headers)
                    status_res.raise_for_status()
                    data = status_res.json()["data"]
                    
                    status = data["status"]
                    if status == "success":
                        model_url = data["output"].get("model")
                        break
                    elif status in ["failed", "cancelled", "timeout"]:
                        raise InferenceError(f"Tripo3D Task failed with status: {status}")
                
                time.sleep(3)
                attempt += 1
                
            if not model_url:
                raise InferenceError("Tripo3D Task timed out after maximum attempts.")

            result = {
                "status": "success",
                "task_id": task_id,
                "mode": "mesh",  # Tripo sort du quad mesh optimisé
                "model_url": model_url,
                "preview_video": None,
                "polycount": "Optimized Quad Mesh",
                "format": "GLB",
                "metadata": {
                    "engine": "Tripo3D-v3"
                }
            }
            
            self._log_usage(engine="cloud:tripo_ai_3d", units=1)
            logger.info("3D Scene successfully generated via Tripo3D API.")
            return result
            
        except Exception as e:
            logger.error(f"Error during 3D generation: {e}")
            from core.domain.exceptions import InferenceError
            raise InferenceError(f"Failed to generate 3D scene: {e}")
