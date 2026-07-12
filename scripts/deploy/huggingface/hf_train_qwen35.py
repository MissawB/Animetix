#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "trl>=0.12.0",
#     "peft>=0.7.0",
#     "transformers>=4.57.0",
#     "accelerate>=0.24.0",
#     "datasets",
#     "trackio",
#     "bitsandbytes",
#     "torch",
# ]
# ///
"""QLoRA SFT of the Otaku expert adapter on Qwen3.5-9B, on Hugging Face Jobs.

Run it with the HF Jobs CLI (the environment is ephemeral -- everything not
pushed to the Hub is lost when the job ends):

    hf jobs uv run --flavor a10g-large --timeout 45m --secrets HF_TOKEN \
        -e SMOKE=1 scripts/deploy/huggingface/hf_train_qwen35.py   # validate
    hf jobs uv run --flavor a100-large --timeout 4h --secrets HF_TOKEN \
        scripts/deploy/huggingface/hf_train_qwen35.py              # real run

Two things this script used to get wrong, both of which silently produced an
adapter nobody could serve:

- It pushed to `otaku-qwen-7b-adapter`. The adapter published under that name is
  a LoRA on unsloth/Qwen2.5-7B-Instruct (see its adapter_config.json) -- a
  DIFFERENT base from the Qwen3.5-9B this script trains on. A LoRA is bound to
  its base's architecture, so the artifact could never be loaded onto the model
  the product actually serves. The 9B run now has its own, honestly named repo.
- `max_steps=100` made every run a smoke test. That is now opt-in via SMOKE=1.

Note on the base: the whole Qwen3.5 family is natively multimodal
(Qwen3_5ForConditionalGeneration) -- there is no text-only variant. That is fine
for a text SFT: the vision tower uses fused `qkv`/`proj`/`linear_fc*` modules, so
the LoRA target_modules below (`q_proj`, `gate_proj`, ...) match the language
tower only and leave the vision encoder untouched.
"""

import os

import torch
import trackio
from datasets import load_dataset
from peft import LoraConfig
from transformers import BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen3.5-9B")
DATASET = os.getenv("DATASET", "MissawB/otaku-expert-dataset")
HUB_MODEL_ID = os.getenv("HUB_MODEL_ID", "MissawB/otaku-qwen35-9b-adapter")
# A smoke run proves the model loads, the collator accepts our text-only samples
# and a step runs -- for a couple of dollars instead of a full a100 run.
SMOKE = os.getenv("SMOKE", "").strip().lower() in ("1", "true", "yes")

SYSTEM_FR = (
    "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des "
    "anime japonais. Tu reponds de maniere tres complete et precise en francais."
)
SYSTEM_EN = (
    "You are Animetix, an absolute expert in otaku culture, Japanese manga and "
    "anime. You answer in a very comprehensive and precise manner in English."
)

print(f"Otaku SFT — base={BASE_MODEL} dataset={DATASET} smoke={SMOKE}")

dataset = load_dataset(DATASET, split="train")
print(f"Dataset loaded: {len(dataset)} examples.")


def to_messages(item):
    """Conversational format: TRL applies the model's chat template itself.

    The previous version pre-rendered the template into a `text` field. Letting
    TRL do it keeps us compatible with the VLM collator this base requires.
    """
    system = SYSTEM_EN if item.get("language") == "English" else SYSTEM_FR
    messages = [{"role": "system", "content": system}]

    if item.get("turns"):
        for turn in item["turns"]:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
    else:
        user_content = item["instruction"]
        if item.get("input"):
            label = "Context" if item.get("language") == "English" else "Contexte"
            user_content = f"{item['instruction']}\n\n{label} : {item['input']}"
        messages.append({"role": "user", "content": user_content})
        messages.append({"role": "assistant", "content": item["output"]})

    return {"messages": messages}


if SMOKE:
    dataset = dataset.select(range(256))

dataset = dataset.map(to_messages, remove_columns=dataset.column_names)
split = dataset.train_test_split(test_size=0.02, seed=42)
train_dataset, eval_dataset = split["train"], split["test"]
print(f"   train={len(train_dataset)}  eval={len(eval_dataset)}")

# 4-bit QLoRA: a 9B base does not fit an a10g in fp16.
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

config = SFTConfig(
    output_dir="otaku-qwen35-9b-adapter",
    push_to_hub=not SMOKE,
    hub_model_id=HUB_MODEL_ID,
    hub_strategy="every_save",
    num_train_epochs=1,
    max_steps=5 if SMOKE else -1,
    # Effective batch 32 -> ~2k steps for one epoch over the 64k examples.
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    gradient_checkpointing=True,
    learning_rate=2e-4,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_strategy="steps",
    save_steps=250,
    save_total_limit=2,
    eval_strategy="no" if SMOKE else "steps",
    eval_steps=250,
    bf16=True,
    report_to="trackio",
    project="animetix-expert",
    run_name="qwen35-9b-otaku-sft" + ("-smoke" if SMOKE else ""),
    # In current TRL these belong to the CONFIG, not to the trainer: passing
    # model_init_kwargs= to SFTTrainer raises TypeError.
    model_init_kwargs={
        "quantization_config": bnb_config,
        "dtype": torch.bfloat16,
        "trust_remote_code": True,
    },
)

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    # Language tower only -- the vision blocks use fused qkv/proj/linear_fc names
    # and are deliberately not matched here.
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
)

trainer = SFTTrainer(
    model=BASE_MODEL,
    train_dataset=train_dataset,
    eval_dataset=None if SMOKE else eval_dataset,
    peft_config=peft_config,
    args=config,
)

trainer.train()

if not SMOKE:
    print(f"Pushing adapter to {HUB_MODEL_ID}...")
    trainer.push_to_hub()

trackio.finish()
print("Done.")
