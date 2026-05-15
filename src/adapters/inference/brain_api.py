import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Ajout du chemin src pour l'import des adapters et ports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.inference.local_llama_adapter import LocalLlamaAdapter
from adapters.inference.vllm_adapter import VllmAdapter

logger = logging.getLogger("brain")

from contextlib import asynccontextmanager

# Configuration des moteurs d'inférence
MODELS_DIR = os.getenv("MODELS_DIR", "data/models")
# On utilise un modèle plus léger et non-gated par défaut pour éviter les erreurs de token/poids
DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
llama_path = os.path.join(MODELS_DIR, "llama-3-8b")

# Fallback si le dossier local n'existe pas
if not os.path.exists(llama_path):
    logger.info(f"📂 Chemin local {llama_path} non trouvé. Utilisation du modèle distant : {DEFAULT_MODEL}")
    llama_path = DEFAULT_MODEL

# Initialisation de l'unité de calcul locale
brain_engine = LocalLlamaAdapter(
    model_path=llama_path,
    hf_token=os.getenv("HUGGINGFACE_TOKEN"),
    use_4bit=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # CHARGEMENT EAGER : On charge le modèle au démarrage pour éviter les timeouts au premier call
    logger.info("🧠 Brain API is warming up... Loading models.")
    try:
        brain_engine._load_model()
        logger.info("✅ Brain API is ready. Model loaded.")
    except Exception as e:
        logger.error(f"❌ Failed to load model during startup: {e}")
    yield
    # Cleanup si besoin

app = FastAPI(title="Animetix Brain API", version="2.0.0", lifespan=lifespan)

class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku."

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
        res = brain_engine.generate(req.prompt, req.system_prompt)
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
