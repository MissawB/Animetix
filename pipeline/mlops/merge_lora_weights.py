import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def merge_lora():
    base_model_name = "unsloth/Llama-3.2-3B-Instruct"
    adapter_path = os.path.join(BASE_DIR, "data", "models", "otaku-llama-adapter", "checkpoint-100")
    output_path = os.path.join(BASE_DIR, "data", "models", "otaku-llama-3.2-3b-final")

    if not os.path.exists(adapter_path):
        print(f"Error: Adapter not found at {adapter_path}. Please train the model first.")
        return

    print(f"Loading base model: {base_model_name}...")
    
    # On charge le modèle en FP16 (ou BF16 si supporté) pour le merge
    # Note: On ne charge PAS en 4-bit pour le merge final car merge_and_unload() ne le supporte pas bien
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="cpu", # On merge sur CPU pour éviter de saturer la VRAM si le modèle est gros
        trust_remote_code=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    print(f"Loading adapter from {adapter_path}...")
    model = PeftModel.from_pretrained(base_model, adapter_path)

    print("Merging weights...")
    merged_model = model.merge_and_unload()

    print(f"Saving merged model to {output_path}...")
    merged_model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    print(f"Successfully merged and saved to {output_path}")

if __name__ == "__main__":
    merge_lora()
