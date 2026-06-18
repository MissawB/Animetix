import os
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Configuration du logger
logger = logging.getLogger("animetix." + __name__)

# Base directory (4 levels up from backend/pipeline/mlops/)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def merge_lora():
    base_model_name = os.getenv(
        "BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-8B"
    )
    adapter_path = os.path.join(
        BASE_DIR, "data", "models", "otaku-expert-adapter", "checkpoint-100"
    )
    output_path = os.path.join(BASE_DIR, "data", "models", "otaku-expert-final")

    if not os.path.exists(adapter_path):
        logger.error(
            f"❌ Error: Adapter not found at {adapter_path}. Please train the model first."
        )
        return

    device_map = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"🚀 Loading base model: {base_model_name} on {device_map}...")

    # On charge le modèle en FP16 (ou BF16 si supporté) pour le merge
    # Note: On ne charge PAS en 4-bit pour le merge final car merge_and_unload() ne le supporte pas bien
    try:
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map=device_map,
            trust_remote_code=True,
            revision="main",
        )  # nosec B615
    except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
        if device_map == "cuda":
            logger.warning(f"⚠️ OutOfMemory on GPU ({e}). Falling back to CPU merge...")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            device_map = "cpu"
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
                device_map=device_map,
                trust_remote_code=True,
                revision="main",
            )  # nosec B615
        else:
            raise e

    tokenizer = AutoTokenizer.from_pretrained(base_model_name, revision="main")  # nosec B615

    logger.info(f"📦 Loading adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path, revision="main")  # nosec B615

    logger.info("🚀 Merging weights...")
    merged_model = model.merge_and_unload()

    logger.info(f"📦 Saving merged model to {output_path}...")
    merged_model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    logger.info(f"✅ Successfully merged and saved to {output_path}")


if __name__ == "__main__":
    merge_lora()
