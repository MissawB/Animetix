import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_expert_training():
    model_name = "unsloth/Llama-3.2-3B-Instruct" 
    dataset_path = os.path.join(BASE_DIR, "data", "mlops", "datasets", "animetix_expert_ft.jsonl")
    output_dir = os.path.join(BASE_DIR, "data", "models", "otaku-llama-adapter")
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found at {dataset_path}. Run finetuning_dataset.py first.")
        return

    print(f"🚀 Starting QLoRA Fine-Tuning for {model_name}...")

    # 1. Chargement du dataset
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    # 2. Configuration Quantisation 4-bit
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 3. Chargement du modèle
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 4. Configuration LoRA
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    # 5. Paramètres d'entraînement
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2, # Réduit pour éviter OOM sur petites GPUs
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        logging_steps=10,
        max_steps=100, 
        save_total_limit=1,
        fp16=True,
        push_to_hub=False,
        report_to="none"
    )

    # Formatting function for Alpaca format
    def formatting_prompts_func(example):
        output_texts = []
        for i in range(len(example['instruction'])):
            text = f"### Instruction:\n{example['instruction'][i]}\n\n### Input:\n{example['input'][i]}\n\n### Response:\n{example['output'][i]}"
            output_texts.append(text)
        return output_texts

    # 6. Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        formatting_func=formatting_prompts_func,
        max_seq_length=1024,
        tokenizer=tokenizer,
        args=training_args,
    )

    trainer.train()
    print(f"✅ Model trained and adapter saved at {output_dir}")

if __name__ == "__main__":
    if torch.cuda.is_available():
        run_expert_training()
    else:
        print("⚠️ CUDA not available. Training script ready but requires GPU.")
