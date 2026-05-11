from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Animetix Brain API")

# Configuration du modèle local expert
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "otaku-llama-3.2-3b-final")

model = None
tokenizer = None

@app.on_event("startup")
def load_expert_model():
    global model, tokenizer
    if os.path.exists(MODEL_PATH):
        try:
            print(f"Loading Local Expert Model: {MODEL_PATH}")
            tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                device_map="auto"
            )
        except Exception as e:
            print(f"Error loading local expert model: {e}")
            print("Falling back to API mode.")
            model = None
            tokenizer = None
    else:
        print("Local Expert Model not found. Falling back to API mode.")

class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku pour la plateforme Animetix."

@app.get("/")
def health_check():
    engine = "Animetix-Expert-Local" if model else "Fallback-API"
    return {"status": "online", "engine": engine}

@app.post("/generate")
async def generate(request: GenerateRequest):
    # 1. Priorité : Modèle Local Expert
    if model and tokenizer:
        try:
            full_prompt = f"### Instruction:\n{request.prompt}\n\n### Response:\n"
            inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=500,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            text = response.split("### Response:\n")[-1].strip()
            return {"text": text}
        except Exception as e:
            print(f"❌ Error during local generation: {e}")

    # 2. Fallback sur Hugging Face API si le local échoue ou est absent
    import requests
    HF_TOKEN = os.getenv("HF_TOKEN")
    if HF_TOKEN:
        HF_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        try:
            hf_res = requests.post(HF_URL, headers=headers, json={
                "inputs": f"<|system|>\n{request.system_prompt}</s>\n<|user|>\n{request.prompt}</s>\n<|assistant|>",
                "parameters": {"max_new_tokens": 500}
            }, timeout=30)
            if hf_res.status_code == 200:
                result = hf_res.json()
                text = result[0].get('generated_text', '') if isinstance(result, list) else result.get('generated_text', '')
                if "<|assistant|>" in text:
                    text = text.split("<|assistant|>")[-1].strip()
                return {"text": text}
        except:
            pass

    return {"text": "Désolé, aucune unité de calcul d'IA n'est disponible."}
