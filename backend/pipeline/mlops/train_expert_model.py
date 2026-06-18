# -*- coding: utf-8 -*-
"""
Script d'entraînement expert QLoRA hautement optimisé intégrant 14 techniques de pointe
pour les architectures GPU à VRAM limitée.
"""

import os  # noqa: E402

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import logging  # noqa: E402
import time  # noqa: E402

import torch  # noqa: E402
from datasets import load_dataset  # noqa: E402
from peft import LoraConfig  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments
from trl import DataCollatorForCompletionOnlyLM, SFTTrainer  # noqa: E402

# Configuration du logger
logger = logging.getLogger("animetix.pipeline.mlops.train_expert")

# Essayer d'importer liger_kernel pour la fusion d'opérateurs Triton
try:
    from liger_kernel.transformers import monkey_patch_liger  # noqa: E402

    monkey_patch_liger()
    logger.info(
        "⚙️ Liger Kernel fused successfully (Triton mathematical operators optimized)."
    )
except ImportError:
    logger.info(
        "ℹ️ Liger Kernel not available, skipping Triton mathematical operator fusion."
    )

# Import hf_trackio pour le suivi MLOps
try:
    from hf_trackio import trackio  # noqa: E402
except ImportError:

    class MockTrackio:
        def log(self, *args, **kwargs):
            pass

        def start_run(self, *args, **kwargs):
            pass

        def end_run(self, *args, **kwargs):
            pass

        def init(self, *args, **kwargs):
            return self

        def finish(self, *args, **kwargs):
            pass

        def log_artifact(self, *args, **kwargs):
            pass

        def log_param(self, *args, **kwargs):
            pass

        def log_metric(self, *args, **kwargs):
            pass

    trackio = MockTrackio()

# Base directory (4 levels up from backend/pipeline/mlops/)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def format_chatml_messages(item) -> list:
    """
    Formate les messages au format ChatML selon la langue du dataset.
    Supporte le mono-tour et le multi-tours.
    """
    language = item.get("language", "Français")
    if language == "English":
        system_prompt = "You are Animetix, an absolute expert in otaku culture, Japanese manga, and anime. You answer in a very comprehensive and precise manner in English."
    else:
        system_prompt = "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des animés japonais. Tu réponds de manière très complète et précise en français."

    messages = [{"role": "system", "content": system_prompt}]

    if "turns" in item:
        for turn in item["turns"]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
    else:
        user_content = item["instruction"]
        if item.get("input"):
            if language == "English":
                user_content = f"{item['instruction']}\n\nContext: {item['input']}"
            else:
                user_content = f"{item['instruction']}\n\nContexte : {item['input']}"
        messages.append({"role": "user", "content": user_content})
        messages.append({"role": "assistant", "content": item["output"]})

    return messages


def run_expert_training():
    model_name = os.getenv("BASE_MODEL_NAME", "unsloth/DeepSeek-R1-Distill-Qwen-8B")
    default_seq_len = 1024 if "deepseek" in model_name.lower() else 768
    max_seq_length = int(os.getenv("MAX_SEQ_LENGTH", str(default_seq_len)))

    dataset_path = os.path.join(
        BASE_DIR, "data", "mlops", "datasets", "animetix_expert_ft.jsonl"
    )
    output_dir = os.path.join(BASE_DIR, "data", "models", "otaku-expert-adapter")

    tracker = trackio.init(
        project="animetix-expert", job_name=f"expert-qlora-{int(time.time())}"
    )

    if not os.path.exists(dataset_path):
        logger.error(
            f"❌ Dataset not found at {dataset_path}. Run finetuning_dataset.py first."
        )
        tracker.finish(status="FAILED")
        return

    logger.info(f"🚀 Starting highly-optimized QLoRA Fine-Tuning for {model_name}...")
    tracker.log_param("model_base", model_name)
    tracker.log_artifact("dataset", dataset_path)

    # 1. Configuration et chargement du tokenizer
    logger.info("📂 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision="main")  # nosec B615
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Chargement et fractionnement Train/Eval (95/05)
    logger.info("📂 Loading and splitting dataset...")
    full_dataset = load_dataset(
        "json", data_files=dataset_path, split="train", revision="main"
    )  # nosec B615
    split_dataset = full_dataset.train_test_split(test_size=0.05, seed=42)
    train_ds = split_dataset["train"]
    eval_ds = split_dataset["test"]
    logger.info(
        f"✅ Dataset loaded: {len(train_ds)} training samples, {len(eval_ds)} validation samples."
    )

    # 3. Application du patron de discussion ChatML natif de Qwen
    logger.info("⚙️ Formatting dataset with native ChatML templates...")

    def process_chatml(item):
        messages = format_chatml_messages(item)
        formatted = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        return {"text": formatted}

    train_ds = train_ds.map(process_chatml, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(process_chatml, remove_columns=eval_ds.column_names)

    # 4. Chargement optimisé via Unsloth (avec repli PEFT/BitsAndBytes standard en cas d'absence ou distribué)
    model = None
    peft_config = None

    local_rank = int(os.environ.get("LOCAL_RANK", "-1"))
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    is_distributed = (
        local_rank != -1
        or world_size > 1
        or (torch.cuda.is_available() and torch.cuda.device_count() > 1)
    )

    try:
        if is_distributed:
            logger.info(
                "ℹ️ Distributed training detected. Bypassing Unsloth to avoid single-GPU constraints."
            )
            raise ImportError("Bypass Unsloth under distributed training")

        from unsloth import FastLanguageModel  # noqa: E402

        logger.info(
            "🚀 Unsloth detected. Loading model with native GPU optimizations..."
        )
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            dtype=None,  # Détection automatique de précision (float16/bfloat16)
            load_in_4bit=True,
            revision="main",
        )  # nosec B615
        # Injection LoRA via Unsloth
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            lora_alpha=32,
            lora_dropout=0.0,  # Unsloth recommande lora_dropout=0 pour des performances optimales
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
            use_rslora=True,  # Rank-Stabilized LoRA activé
        )
        logger.info(
            "✅ Model loaded and LoRA adapters injected using Unsloth FastLanguageModel."
        )
    except ImportError:
        logger.info(
            "ℹ️ Unsloth not available or bypassed. Falling back to standard Hugging Face PEFT + BitsAndBytesConfig/Full precision..."
        )

        device_map = {"": local_rank} if local_rank != -1 else "auto"
        disable_quant = (
            os.getenv("ANIMETIX_DISABLE_QUANT", "False").lower() in ("true", "1", "yes")
            or is_distributed
        )

        if disable_quant:
            logger.info(
                "Loading model in full/mixed precision (no quantization) for distributed training compatibility..."
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=device_map,
                torch_dtype=(
                    torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
                ),
                trust_remote_code=True,
                low_cpu_mem_usage=True if device_map == "auto" else False,
                revision="main",
            )  # nosec B615
        else:
            logger.info("Loading model with standard 4-bit quantization...")
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                revision="main",
            )  # nosec B615

        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()

        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            lora_dropout=0.05,
            bias="none",
            use_rslora=True,  # Rank-Stabilized LoRA activé
            task_type="CAUSAL_LM",
        )
        logger.info("✅ Model loaded with standard PEFT configuration.")

    # 5. Assistant-Only Loss Masking (Data Collator ciblant uniquement la réponse de l'assistant)
    # Validation dynamique du patron pour éviter les échecs de tokenisation silencieux
    enable_packing = os.getenv("ANIMETIX_PACKING", "False").lower() in (
        "true",
        "1",
        "yes",
    )

    collator = None
    if enable_packing:
        logger.info(
            "📦 Sequence Packing is enabled. Bypassing DataCollatorForCompletionOnlyLM to prevent TRL conflicts."
        )
    else:
        logger.info("🔍 Checking DataCollator response template tokenization...")
        test_messages = [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Réponse"},
        ]
        test_text = tokenizer.apply_chat_template(test_messages, tokenize=False)
        test_tokenized = tokenizer(test_text, return_tensors="pt")

        possible_templates = [
            "<|im_start|>assistant\n",
            "<|im_start|>assistant",
            "assistant\n",
            "assistant",
        ]

        for template in possible_templates:
            try:
                candidate_collator = DataCollatorForCompletionOnlyLM(
                    response_template=template, tokenizer=tokenizer
                )
                outputs = candidate_collator.torch_call(
                    [test_tokenized["input_ids"][0].tolist()]
                )
                labels = outputs["labels"][0]
                trained_tokens = (labels != -100).sum().item()
                if trained_tokens > 0:
                    logger.info(
                        f"✅ DataCollator validated with template: {repr(template)} ({trained_tokens} tokens trained)"
                    )
                    collator = candidate_collator
                    break
            except Exception as e:
                logger.debug(f"Failed template {repr(template)}: {e}")

        if collator is None:
            logger.warning(
                "⚠️ Warning: DataCollator template verification failed for all options. Falling back to standard DataCollator (training on prompts too to prevent crash)."
            )
            from transformers import DataCollatorForLanguageModeling  # noqa: E402

            collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # 6. Configuration des hyperparamètres d'entraînement de pointe
    # Batch size=1 avec gradient accumulation=8 permet d'atteindre un batch virtuel stable de 8
    # Paged AdamW 8-bit prévient les pannes de VRAM locale, standard adamw_torch utilisé en distribué
    enable_eval = os.getenv("ANIMETIX_ENABLE_EVAL", "False").lower() in (
        "true",
        "1",
        "yes",
    )
    eval_strategy = "steps" if enable_eval else "no"
    eval_steps = 100 if enable_eval else 9999

    if enable_eval:
        logger.info(
            f"📊 Evaluation activated: strategy={eval_strategy}, steps={eval_steps}"
        )
    else:
        logger.info(
            "ℹ️ Evaluation deactivated to conserve VRAM (set env ANIMETIX_ENABLE_EVAL=True to enable)."
        )

    optim = "adamw_torch" if is_distributed else "paged_adamw_8bit"
    deepspeed_config = os.getenv("ANIMETIX_DEEPSPEED_CONFIG", None)
    fsdp_config_env = os.getenv("ANIMETIX_FSDP_CONFIG", None)

    training_args_kwargs = dict(
        output_dir=output_dir,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_ratio=0.03,
        max_steps=2500,
        learning_rate=2e-4,
        logging_steps=1,
        eval_strategy=eval_strategy,
        eval_steps=eval_steps,
        save_strategy="steps",
        save_steps=5,
        save_total_limit=1,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        optim=optim,
        lr_scheduler_type="cosine",  # Décroissance cosinusoïdale de pointe
        weight_decay=0.01,
        report_to="none",
        neftune_noise_alpha=5.0,  # NEFTune pour la robustesse et la diversité linguistique
    )

    if is_distributed:
        if deepspeed_config and os.path.exists(deepspeed_config):
            logger.info(f"Injecting DeepSpeed configuration path: {deepspeed_config}")
            training_args_kwargs["deepspeed"] = deepspeed_config
        elif fsdp_config_env:
            logger.info(f"Injecting FSDP configuration parameters: {fsdp_config_env}")
            training_args_kwargs["fsdp"] = fsdp_config_env
            training_args_kwargs["fsdp_config"] = {
                "transformer_layer_cls_to_wrap": os.getenv(
                    "ANIMETIX_FSDP_WRAP_CLASS", "Qwen2DecoderLayer"
                ),
            }

    training_args = TrainingArguments(**training_args_kwargs)

    # 7. Initialisation du SFTTrainer de TRL
    trainer = SFTTrainer(
        model=model,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        tokenizer=tokenizer,
        data_collator=collator,
        args=training_args,
        packing=enable_packing,
    )

    # Lancement de l'entraînement
    logger.info("🚀 Launching training steps...")
    trainer.train()

    tracker.log_artifact("adapter", output_dir)
    tracker.finish(status="COMPLETED")
    logger.info(f"✅ Model successfully trained and adapter saved at {output_dir}")


if __name__ == "__main__":
    if torch.cuda.is_available():
        run_expert_training()
    else:
        logger.warning(
            "⚠️ CUDA is not available. This training script is optimized and ready for GPU execution."
        )
