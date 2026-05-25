# -*- coding: utf-8 -*-
"""
Script d'entraînement expert QLoRA hautement optimisé intégrant 14 techniques de pointe
pour les architectures GPU à VRAM limitée.
"""

import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import sys
import torch
import time
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

# Essayer d'importer liger_kernel pour la fusion d'opérateurs Triton
try:
    from liger_kernel.transformers import monkey_patch_liger
    monkey_patch_liger()
    print("[INFO] Liger Kernel fused successfully (Triton mathematical operators optimized).")
except ImportError:
    print("[INFO] Liger Kernel not available, skipping Triton mathematical operator fusion.")

# Import hf_trackio pour le suivi MLOps
try:
    from hf_trackio import trackio
except ImportError:
    class MockTrackio:
        def log(self, *args, **kwargs): pass
        def start_run(self, *args, **kwargs): pass
        def end_run(self, *args, **kwargs): pass
        def init(self, *args, **kwargs): return self
        def finish(self, *args, **kwargs): pass
        def log_artifact(self, *args, **kwargs): pass
        def log_param(self, *args, **kwargs): pass
        def log_metric(self, *args, **kwargs): pass
    trackio = MockTrackio()

# Base directory (4 levels up from src/pipeline/mlops/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_expert_training():
    model_name = "unsloth/Qwen2.5-7B-Instruct" 
    dataset_path = os.path.join(BASE_DIR, "data", "mlops", "datasets", "animetix_expert_ft.jsonl")
    output_dir = os.path.join(BASE_DIR, "data", "models", "otaku-qwen-7b-adapter")
    
    tracker = trackio.init(project="animetix-expert", job_name=f"expert-qlora-{int(time.time())}")

    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset not found at {dataset_path}. Run finetuning_dataset.py first.")
        tracker.finish(status="FAILED")
        return

    print(f"[INFO] Starting highly-optimized QLoRA Fine-Tuning for {model_name}...")
    tracker.log_param("model_base", model_name)
    tracker.log_artifact("dataset", dataset_path)

    # 1. Configuration et chargement du tokenizer
    print("[INFO] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Chargement et fractionnement Train/Eval (95/05)
    print("[INFO] Loading and splitting dataset...")
    full_dataset = load_dataset("json", data_files=dataset_path, split="train")
    split_dataset = full_dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split_dataset["train"]
    eval_ds = split_dataset["test"]
    print(f"[SUCCESS] Dataset loaded: {len(train_ds)} training samples, {len(eval_ds)} validation samples.")

    # 3. Application du patron de discussion ChatML natif de Qwen
    print("[INFO] Formatting dataset with native ChatML templates...")
    def process_chatml(item):
        user_content = item["instruction"]
        if item["input"]:
            user_content = f"{item['instruction']}\n\nContexte : {item['input']}"
            
        messages = [
            {"role": "system", "content": "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des animés japonais. Tu réponds de manière très complète et précise en français."},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": item["output"]}
        ]
        formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return {"text": formatted}

    train_ds = train_ds.map(process_chatml, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(process_chatml, remove_columns=eval_ds.column_names)

    # 4. Chargement optimisé via Unsloth (avec repli PEFT/BitsAndBytes standard en cas d'absence)
    model = None
    peft_config = None
    
    try:
        from unsloth import FastLanguageModel
        print("[INFO] Unsloth detected. Loading model with native GPU optimizations...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=768,
            dtype=None,  # Détection automatique de précision (float16/bfloat16)
            load_in_4bit=True,
        )
        # Injection LoRA via Unsloth
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=32,
            lora_dropout=0.0,  # Unsloth recommande lora_dropout=0 pour des performances optimales
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
            use_rslora=True,   # Rank-Stabilized LoRA activé
        )
        print("[SUCCESS] Model loaded and LoRA adapters injected using Unsloth FastLanguageModel.")
    except ImportError:
        print("[INFO] Unsloth not available. Falling back to standard Hugging Face PEFT + BitsAndBytesConfig...")
        
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
        
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            use_rslora=True,   # Rank-Stabilized LoRA activé
            task_type="CAUSAL_LM",
        )
        print("[SUCCESS] Model loaded with standard BitsAndBytes and PEFT configuration.")

    # 5. Assistant-Only Loss Masking (Data Collator ciblant uniquement la réponse de l'assistant)
    response_template = "<|im_start|>assistant\n"
    collator = DataCollatorForCompletionOnlyLM(
        response_template=response_template,
        tokenizer=tokenizer
    )

    # 6. Configuration des hyperparamètres d'entraînement de pointe
    # Batch size=1 avec gradient accumulation=8 permet d'atteindre un batch virtuel stable de 8
    # Paged AdamW 8-bit prévient les pannes de VRAM locale
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_ratio=0.03,
        max_steps=2500,
        learning_rate=2e-4,
        logging_steps=1,
        eval_strategy="no",
        eval_steps=9999,  # Désactivé pour préserver la VRAM sur GPU portable
        save_strategy="steps",
        save_steps=5,
        save_total_limit=1,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",  # Optimiseur avec déchargement sur RAM
        lr_scheduler_type="cosine",  # Décroissance cosinusoïdale de pointe
        weight_decay=0.01,
        report_to="none",
        neftune_noise_alpha=5.0,  # NEFTune pour la robustesse et la diversité linguistique
    )

    # 7. Initialisation du SFTTrainer de TRL
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=768,
        tokenizer=tokenizer,
        data_collator=collator,
        args=training_args,
    )

    # Lancement de l'entraînement
    print("[INFO] Launching training steps...")
    trainer.train()
    
    tracker.log_artifact("adapter", output_dir)
    tracker.finish(status="COMPLETED")
    print(f"[SUCCESS] Model successfully trained and adapter saved at {output_dir}")

if __name__ == "__main__":
    if torch.cuda.is_available():
        run_expert_training()
    else:
        print("[WARNING] CUDA is not available. This training script is optimized and ready for GPU execution.")
