import os
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

# Base directory (4 levels up from backend/pipeline/mlops/)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def test_inference():
    model_path = os.path.join(BASE_DIR, "data", "models", "otaku-qwen-7b-final")

    if not os.path.exists(model_path):
        logger.error(
            f"❌ Merged model not found at {model_path}. Waiting for merge to complete..."
        )
        return

    logger.info(f"📂 Loading Expert Model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, revision="main")  # nosec B615
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16, device_map="auto", revision="main"
    )  # nosec B615

    test_queries = [
        "Présente l'anime 'Cowboy Bebop' de manière détaillée.",
        "Qui est le studio derrière 'Spirited Away' ?",
        "Analyse le personnage de Levi Ackerman dans Attack on Titan.",
        "Quelles sont les thématiques principales du manga 'Berserk' ?",
    ]

    logger.info("--- Expert Evaluation Phase ---")

    for query in test_queries:
        logger.info(f"Question: {query}")
        prompt = f"### Instruction:\n{query}\n\n### Response:\n"
        inputs = tokenizer(prompt, return_tensors="pt").to(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        clean_response = response.split("### Response:\n")[-1]
        logger.info(f"Answer: {clean_response}")
        logger.info("-" * 50)


if __name__ == "__main__":
    test_inference()
