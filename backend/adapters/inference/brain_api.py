import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Ajout du chemin src pour l'import des adapters et ports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter

logger = logging.getLogger("animetix.brain")

from contextlib import asynccontextmanager

# Configuration des moteurs d'inférence
api_base = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
model_name = os.getenv("LLM_MODEL_NAME", "llama3")

# Initialisation de l'unité de calcul locale (Ollama)
brain_engine = UnifiedInferenceAdapter(
    api_base=api_base,
    model_name=model_name
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🧠 Brain API is using Ollama at {api_base} with model {model_name}")
    yield
    # Cleanup si besoin

app = FastAPI(title="Animetix Brain API", version="2.0.0", lifespan=lifespan)

class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku."
    thinking_budget: int = 0
    thinking_mode: bool = False

class SimilarityRequest(BaseModel):
    query: str
    item_id: str
    media_type: str

@app.get("/health")
def health():
    return brain_engine.health_check()

@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        res = brain_engine.generate(
            req.prompt, 
            req.system_prompt, 
            thinking_budget=req.thinking_budget, 
            thinking_mode=req.thinking_mode
        )
        return {"text": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/similarity/visual")
def visual_similarity(req: SimilarityRequest):
    try:
        score = brain_engine.calculate_visual_similarity(req.query, req.item_id, req.media_type)
        return {"score": score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/embed")
async def embed_image(image: UploadFile = File(...), model_id: Optional[str] = None):
    try:
        data = await image.read()
        emb = brain_engine.get_image_embedding(data, model_id)
        return {"embedding": emb}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7861)
