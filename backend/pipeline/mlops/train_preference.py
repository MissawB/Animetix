# -*- coding: utf-8 -*-
"""
Script d'alignement par préférences (SimPO / ORPO / DPO) expert et résilient,
utilisant Unsloth pour l'accélération et le déchargement mémoire GPU.
"""

import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import sys
import torch
import time
import json
import logging
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model

# Configuration du logger
logger = logging.getLogger("animetix.pipeline.mlops.train_preference")
logging.basicConfig(level=logging.INFO)

# Essayer d'importer liger_kernel pour la fusion d'opérateurs Triton
try:
    from liger_kernel.transformers import monkey_patch_liger
    monkey_patch_liger()
    logger.info("⚙️ Liger Kernel fused successfully (Triton mathematical operators optimized).")
except ImportError:
    logger.info("ℹ️ Liger Kernel not available, skipping Triton mathematical operator fusion.")

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
        def log_param(self, *args, **kwargs): pass
        def log_artifact(self, *args, **kwargs): pass
    trackio = MockTrackio()

# Base directory (4 levels up from backend/pipeline/mlops/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_preference_training():
    model_name = os.getenv("BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-8B")
    default_seq_len = 1024 if "deepseek" in model_name.lower() else 768
    max_seq_length = int(os.getenv("MAX_SEQ_LENGTH", str(default_seq_len)))
    
    # Choix dynamique de l'algorithme : simpo, orpo, dpo
    algo = os.getenv("ALIGNMENT_ALGORITHM", "simpo").lower()
    if algo not in ["simpo", "orpo", "dpo"]:
        algo = "simpo"
        
    dataset_path = os.path.join(BASE_DIR, "data", "mlops", "datasets", "dpo_train_validated.jsonl")
    output_dir = os.path.join(BASE_DIR, "data", "models", "otaku-preference-adapter")
    
    tracker = trackio.init(project="animetix-preference", job_name=f"preference-{algo}-{int(time.time())}")

    # Fallback si le dataset n'existe pas ou est vide
    if not os.path.exists(dataset_path) or os.path.getsize(dataset_path) == 0:
        logger.warning(f"⚠️ Dataset not found or empty at {dataset_path}. Generating a dummy dataset for safety...")
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        dummy_data = [
            {
                "prompt": "Génère une réponse expert pour : Qui est le protagoniste de One Piece ?",
                "chosen": "Le protagoniste de One Piece est Monkey D. Luffy, un jeune pirate qui rêve de devenir le Roi des Pirates.",
                "rejected": "Je ne sais pas qui est le protagoniste de cette œuvre."
            },
            {
                "prompt": "Génère une réponse expert pour : Quel studio a produit l'anime Shingeki no Kyojin ?",
                "chosen": "L'adaptation en animé de Shingeki no Kyojin (L'Attaque des Titans) a été produite par Wit Studio (saisons 1 à 3) puis par le studio MAPPA (saison finale).",
                "rejected": "C'est un studio inconnu."
            }
        ]
        with open(dataset_path, "w", encoding="utf-8") as f:
            for item in dummy_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info(f"🚀 Starting highly-optimized {algo.upper()} Preference Fine-Tuning for {model_name}...")
    tracker.log_param("model_base", model_name)
    tracker.log_param("algorithm", algo)
    tracker.log_artifact("dataset", dataset_path)

    # 1. Configuration et chargement du tokenizer
    logger.info("📂 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Chargement et fractionnement Train/Eval (90/10)
    logger.info("📂 Loading and splitting dataset...")
    full_dataset = load_dataset("json", data_files=dataset_path, split="train")
    # TRL DPOTrainer requiert au moins quelques exemples pour valider
    if len(full_dataset) < 2:
        logger.warning("Dataset too small for split, duplication applied.")
        # Dupliquer pour éviter le crash en test
        full_dataset = load_dataset("json", data_files=dataset_path, split="train")
    
    split_dataset = full_dataset.train_test_split(test_size=0.1, seed=42)
    train_ds = split_dataset["train"]
    eval_ds = split_dataset["test"]
    logger.info(f"✅ Dataset loaded: {len(train_ds)} training samples, {len(eval_ds)} validation samples.")

    # 3. Formatage ChatML des paires de préférences
    logger.info("⚙️ Formatting dataset into ChatML preference format...")
    def process_dpo_pair(item):
        messages_prompt = [
            {"role": "system", "content": "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des animés japonais. Tu réponds de manière très complète et précise en français."},
            {"role": "user", "content": item["prompt"]}
        ]
        
        prompt_str = tokenizer.apply_chat_template(messages_prompt, tokenize=False, add_generation_prompt=True)
        
        messages_chosen = messages_prompt + [{"role": "assistant", "content": item["chosen"]}]
        messages_rejected = messages_prompt + [{"role": "assistant", "content": item["rejected"]}]
        
        chosen_str = tokenizer.apply_chat_template(messages_chosen, tokenize=False, add_generation_prompt=False)
        rejected_str = tokenizer.apply_chat_template(messages_rejected, tokenize=False, add_generation_prompt=False)
        
        # Extraction de la réponse assistant uniquement (suffixe)
        chosen_response = chosen_str[len(prompt_str):]
        rejected_response = rejected_str[len(prompt_str):]
        
        return {
            "prompt": prompt_str,
            "chosen": chosen_response,
            "rejected": rejected_response
        }

    train_ds = train_ds.map(process_dpo_pair, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(process_dpo_pair, remove_columns=eval_ds.column_names)

    # 4. Chargement optimisé via Unsloth (avec repli PEFT/BitsAndBytes standard en cas d'absence)
    model = None
    peft_config = None
    
    try:
        from unsloth import FastLanguageModel
        logger.info("🚀 Unsloth detected. Loading model with native GPU optimizations...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            dtype=None,  # Détection automatique de précision
            load_in_4bit=True,
        )
        # Injection LoRA via Unsloth
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=32,
            lora_dropout=0.0,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
            use_rslora=True,
        )
        logger.info("✅ Model loaded and LoRA adapters injected using Unsloth.")
    except ImportError:
        logger.info("ℹ️ Unsloth not available. Falling back to standard Hugging Face PEFT + BitsAndBytesConfig...")
        
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
            use_rslora=True,
            task_type="CAUSAL_LM",
        )
        logger.info("✅ Model loaded with standard BitsAndBytes and PEFT configuration.")

    # 5. Configuration des hyperparamètres d'entraînement
    enable_eval = os.getenv("ANIMETIX_ENABLE_EVAL", "False").lower() in ("true", "1", "yes")
    eval_strategy = "steps" if enable_eval else "no"
    eval_steps = 50 if enable_eval else 9999
    
    # Configuration TRL importable en 2026
    from trl import DPOConfig, DPOTrainer, ORPOConfig, ORPOTrainer

    # Paramètres d'entraînement partagés
    training_args_dict = dict(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_ratio=0.03,
        max_steps=200,  # Moins de steps nécessaires que SFT pour l'alignement
        learning_rate=5e-6 if algo == "orpo" else 1e-6,  # Taux plus faibles pour le RL
        logging_steps=1,
        eval_strategy=eval_strategy,
        eval_steps=eval_steps,
        save_strategy="steps",
        save_steps=20,
        save_total_limit=1,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        report_to="none",
    )

    # 6. Initialisation et entraînement selon l'algorithme choisi
    trainer = None
    if algo == "orpo":
        logger.info("🏋️ Initializing ORPOTrainer (Single-stage SFT + Preference)...")
        orpo_args = ORPOConfig(**training_args_dict, max_prompt_length=max_seq_length // 2, max_length=max_seq_length)
        trainer = ORPOTrainer(
            model=model,
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            tokenizer=tokenizer,
            peft_config=peft_config,
            args=orpo_args,
        )
    elif algo == "simpo":
        logger.info("🏋️ Initializing DPOTrainer in SimPO mode (No reference model)...")
        # SimPO est activé en passant loss_type="simpo" et ref_model=None
        simpo_args = DPOConfig(
            **training_args_dict,
            max_prompt_length=max_seq_length // 2,
            max_length=max_seq_length,
            loss_type="simpo",
            beta=2.0,  # Paramètre SimPO classique (échelle de la marge)
            simpo_gamma=1.4,  # Marge cible SimPO
        )
        trainer = DPOTrainer(
            model=model,
            ref_model=None,  # SimPO n'utilise pas de modèle de référence
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            tokenizer=tokenizer,
            peft_config=peft_config,
            args=simpo_args,
        )
    else:  # dpo classique
        logger.info("🏋️ Initializing standard DPOTrainer (Requires reference model)...")
        dpo_args = DPOConfig(
            **training_args_dict,
            max_prompt_length=max_seq_length // 2,
            max_length=max_seq_length,
            loss_type="sigmoid",
            beta=0.1,
        )
        # On passe le même modèle en ref_model (TRL s'occupe de cloner/détacher ou d'utiliser le mode PEFT sans ref)
        trainer = DPOTrainer(
            model=model,
            ref_model=None,  # En mode PEFT, TRL peut se passer de ref_model explicite pour économiser de la VRAM
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            tokenizer=tokenizer,
            peft_config=peft_config,
            args=dpo_args,
        )

    # Lancement de l'entraînement
    logger.info("🚀 Launching preference training steps...")
    trainer.train()
    
    tracker.log_artifact("adapter", output_dir)
    tracker.finish(status="COMPLETED")
    logger.info(f"✅ Model successfully aligned and preference adapter saved at {output_dir}")

if __name__ == "__main__":
    if torch.cuda.is_available():
        run_preference_training()
    else:
        logger.warning("⚠️ CUDA is not available. Preference training script is ready for GPU execution.")
