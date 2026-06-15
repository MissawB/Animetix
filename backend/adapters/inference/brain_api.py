import os
import sys
import logging
import base64
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Ajout du chemin src pour l'import des adapters et ports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'api'))

from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter

logger = logging.getLogger("animetix.brain")

# --- AUTHENTICATION ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

EXPECTED_API_KEY = os.getenv("BRAIN_API_KEY")
DEV_INSECURE_KEY = "dev-insecure-key-animetix-2026"

if not EXPECTED_API_KEY or EXPECTED_API_KEY == DEV_INSECURE_KEY:
    logger.critical("FATAL: BRAIN_API_KEY non configurée ou non sécurisée. Le cerveau ne peut pas démarrer.")
    sys.exit(1)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key

from contextlib import asynccontextmanager

# Configuration des moteurs d'inférence
api_base = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
model_name = os.getenv("LLM_MODEL_NAME", "llama3")

# Initialisation de l'unité de calcul locale (Unified avec GPU)
brain_engine = UnifiedInferenceAdapter(
    api_base=api_base,
    model_name=model_name
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing telemetry for brain-api...")
    try:
        from animetix.telemetry import init_telemetry
        init_telemetry("animetix-brain")
    except Exception as e:
        logger.warning(f"Could not initialize telemetry: {e}")
    logger.info(f"🧠 Brain API running with engine {model_name}")
    yield

app = FastAPI(title="Animetix Brain API", version="2.0.0", lifespan=lifespan)

# --- SCHÉMAS DE REQUÊTES PYDANTIC ---

class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku."
    thinking_budget: int = 0
    thinking_mode: bool = False
    include_logprobs: bool = False

class SimilarityRequest(BaseModel):
    query: str
    item_id: str
    media_type: str

class Base64ImageRequest(BaseModel):
    image: str
    model_id: Optional[str] = None

class DetectRequest(BaseModel):
    image: str
    candidate_labels: List[str]
    model_id: Optional[str] = None

class DescribeImageRequest(BaseModel):
    image: str
    prompt: str = ""

class RerankRequest(BaseModel):
    query: str
    image_urls: List[str]
    system_prompt: str = ""

class ClassifyRequest(BaseModel):
    image: str
    candidate_labels: List[str]
    model_id: Optional[str] = None

class VideoRequest(BaseModel):
    video: str
    prompt: str = ""

class DocumentRerankRequest(BaseModel):
    query: str
    documents: List[str]

class VideoLocalizeRequest(BaseModel):
    video: str
    queries: List[str]

class TransformRequest(BaseModel):
    image: str
    studio_style: str
    prompt: str = ""

class VideoTransformRequest(BaseModel):
    video: str
    studio_style: str
    prompt: str = ""

class SoundscapeRequest(BaseModel):
    video_metadata: Dict[str, Any]
    prompt: Optional[str] = None

class CloneVoiceRequest(BaseModel):
    text: str
    reference_audio: str  # base64
    language: str = "fr"

class SpeechToSpeechRequest(BaseModel):
    audio: str  # base64
    system_prompt: str = ""

class MangaTranslateRequest(BaseModel):
    image: str
    target_lang: str = "Français"

class MangaInpaintRequest(BaseModel):
    image: str
    text_placements: List[Dict[str, Any]]

class DiagnosticsRequest(BaseModel):
    prompt: str
    completion: str

class UncertaintyRequest(BaseModel):
    prompt: str
    completion: str

class Generate3DRequest(BaseModel):
    image: str
    depth_map: str

class ModerateRequest(BaseModel):
    text: str
    categories: List[str]

class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = ""

# --- ENDPOINTS ---

@app.middleware("http")
async def add_process_trace_context(request: Request, call_next):
    # Extract trace context from request headers
    headers = {k.lower(): v for k, v in request.headers.items()}
    
    try:
        from animetix.telemetry import extract_trace_context
        from opentelemetry import trace
        from opentelemetry.trace import Status, StatusCode
        
        context = extract_trace_context(headers)
        tracer = trace.get_tracer("animetix.brain.request")
        span_name = f"HTTP {request.method} {request.url.path}"
        
        with tracer.start_as_current_span(span_name, context=context) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            
            try:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, description=f"HTTP {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))
                return response
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, description=str(e)))
                raise e
    except ImportError:
        # Fallback if telemetry libraries are not available
        return await call_next(request)

@app.get("/health")
def health():
    return brain_engine.health_check()

@app.post("/generate", dependencies=[Depends(verify_api_key)])
def generate(req: GenerateRequest):
    try:
        res = brain_engine.generate(
            req.prompt, 
            req.system_prompt, 
            thinking_budget=req.thinking_budget, 
            thinking_mode=req.thinking_mode,
            include_logprobs=req.include_logprobs
        )
        return {
            "text": res.text,
            "usage": res.metadata.usage if res.metadata else {},
            "logprobs": [
                {
                    "token": lp.token,
                    "logprob": lp.logprob,
                    "top_logprobs": lp.top_logprobs
                } for lp in res.metadata.logprobs
            ] if res.metadata and res.metadata.logprobs else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/similarity/visual", dependencies=[Depends(verify_api_key)])
def visual_similarity(req: SimilarityRequest):
    try:
        score = brain_engine.calculate_visual_similarity(req.query, req.item_id, req.media_type)
        return {"score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/embedding", dependencies=[Depends(verify_api_key)])
def vision_embedding(req: Base64ImageRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        emb = brain_engine.get_image_embedding(img_bytes, req.model_id)
        return {"embedding": emb}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/detect", dependencies=[Depends(verify_api_key)])
def vision_detect(req: DetectRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        objects = brain_engine.detect_objects(img_bytes, req.candidate_labels, req.model_id)
        return {"objects": objects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/describe", dependencies=[Depends(verify_api_key)])
def vision_describe(req: DescribeImageRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        desc = brain_engine.generate_image_description(img_bytes, req.prompt)
        return {"description": desc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video/describe", dependencies=[Depends(verify_api_key)])
def video_describe(req: VideoRequest):
    try:
        vid_bytes = base64.b64decode(req.video)
        desc = brain_engine.generate_video_description(vid_bytes, req.prompt)
        return {"description": desc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/rerank", dependencies=[Depends(verify_api_key)])
def rerank_documents(req: DocumentRerankRequest):
    try:
        scores = brain_engine.rerank_documents(req.query, req.documents)
        return {"scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/depth", dependencies=[Depends(verify_api_key)])
def vision_depth(req: Base64ImageRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        depth_bytes = brain_engine.estimate_depth(img_bytes)
        depth_b64 = base64.b64encode(depth_bytes).decode('utf-8')
        return {"depth_b64": depth_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/rerank", dependencies=[Depends(verify_api_key)])
def vision_rerank(req: RerankRequest):
    try:
        items = brain_engine.visual_rerank(req.query, req.image_urls, req.system_prompt)
        return {"reranked_items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/classify", dependencies=[Depends(verify_api_key)])
def vision_classify(req: ClassifyRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        labels = brain_engine.classify_image(img_bytes, req.candidate_labels, req.model_id)
        return {"labels": labels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video/embeddings", dependencies=[Depends(verify_api_key)])
def video_embeddings(req: VideoRequest):
    try:
        vid_bytes = base64.b64decode(req.video)
        embs = brain_engine.get_video_temporal_embeddings(vid_bytes)
        return {"embeddings": embs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video/localize", dependencies=[Depends(verify_api_key)])
def video_localize(req: VideoLocalizeRequest):
    try:
        vid_bytes = base64.b64decode(req.video)
        actions = brain_engine.localize_video_actions(vid_bytes, req.queries)
        return {"actions": actions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/transform/anime", dependencies=[Depends(verify_api_key)])
def transform_image_anime(req: TransformRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        res = brain_engine.transform_image_to_anime(img_bytes, req.studio_style, req.prompt)
        return {"image_url_or_b64": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/video/transform/anime", dependencies=[Depends(verify_api_key)])
def transform_video_anime(req: VideoTransformRequest):
    try:
        vid_bytes = base64.b64decode(req.video)
        res = brain_engine.transform_video_to_anime(vid_bytes, req.studio_style, req.prompt)
        return {"video_url_or_b64": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audio/generate/soundscape", dependencies=[Depends(verify_api_key)])
def generate_soundscape(req: SoundscapeRequest):
    try:
        res = brain_engine.generate_soundscape(req.video_metadata, req.prompt)
        return {"audio_url_or_b64": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audio/clone-voice", dependencies=[Depends(verify_api_key)])
def clone_voice(req: CloneVoiceRequest):
    try:
        ref_bytes = base64.b64decode(req.reference_audio)
        audio_bytes = brain_engine.clone_voice(req.text, ref_bytes, req.language)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {"audio_b64": audio_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audio/speech-to-speech", dependencies=[Depends(verify_api_key)])
def speech_to_speech(req: SpeechToSpeechRequest):
    try:
        aud_bytes = base64.b64decode(req.audio)
        audio_bytes = brain_engine.speech_to_speech(aud_bytes, req.system_prompt)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return {"audio_b64": audio_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/manga/process", dependencies=[Depends(verify_api_key)])
def process_manga_page(req: Base64ImageRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        res = brain_engine.process_manga_page(img_bytes)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/manga/translate", dependencies=[Depends(verify_api_key)])
def translate_manga_page(req: MangaTranslateRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        res = brain_engine.translate_manga_page(img_bytes, req.target_lang)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/manga/inpaint", dependencies=[Depends(verify_api_key)])
def inpaint_manga_page(req: MangaInpaintRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        res = brain_engine.inpaint_text_bubbles(img_bytes, req.text_placements)
        return {"image_url_or_b64": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/diagnostics", dependencies=[Depends(verify_api_key)])
def diagnostics(req: DiagnosticsRequest):
    try:
        res = brain_engine.get_diagnostics(req.prompt, req.completion)
        return {"diagnostics": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/uncertainty", dependencies=[Depends(verify_api_key)])
def uncertainty(req: UncertaintyRequest):
    try:
        res = brain_engine.calculate_uncertainty(req.prompt, req.completion)
        return {"uncertainty_metrics": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/generate-3d", dependencies=[Depends(verify_api_key)])
def generate_3d(req: Generate3DRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        depth_bytes = base64.b64decode(req.depth_map)
        res = brain_engine.generate_3d_scene(img_bytes, depth_bytes)
        return {"scene_data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/moderate", dependencies=[Depends(verify_api_key)])
def moderate(req: ModerateRequest):
    try:
        res = brain_engine.moderate_content(req.text, req.categories)
        return {"moderation": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/late-interaction", dependencies=[Depends(verify_api_key)])
def vision_late_interaction(req: Base64ImageRequest):
    try:
        img_bytes = base64.b64decode(req.image)
        res = brain_engine.get_multimodal_late_interaction(img_bytes)
        return {"embeddings": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/generate", dependencies=[Depends(verify_api_key)])
def vision_generate(req: ImageGenerateRequest):
    try:
        res = brain_engine.generate_image(req.prompt, req.style)
        return {"image_url_or_b64": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    host = os.getenv("BRAIN_API_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=7861)
