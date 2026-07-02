#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "trl>=0.12.0",
#     "peft>=0.7.0",
#     "transformers>=4.45.0",
#     "accelerate>=0.24.0",
#     "datasets",
#     "trackio",
#     "bitsandbytes",
#     "torch",
# ]
# ///

import torch
import trackio
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

print("Starting Hugging Face Job for Otaku Reasoning Qwen 3.5 9B Fine-Tuning...")

# 1. Load Dataset
print("Loading dataset from Hugging Face Hub...")
dataset = load_dataset("MissawB/otaku-expert-dataset", split="train")
print(f"Dataset loaded: {len(dataset)} examples.")

# Split dataset for train/eval
dataset_split = dataset.train_test_split(test_size=0.05, seed=42)
train_dataset = dataset_split["train"]
eval_dataset = dataset_split["test"]
print(f"   Train split: {len(train_dataset)} examples.")
print(f"   Eval split: {len(eval_dataset)} examples.")

# 2. Tokenizer setup
print("Loading Qwen 3.5 9B Tokenizer...")
model_id = "Qwen/Qwen3.5-9B"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# 3. Format ChatML
print("Preprocessing dataset into native ChatML format...")


def process_chatml(item):
    language = item.get("language", "Francais")
    if language == "English":
        system_prompt = "You are Animetix, an absolute expert in otaku culture, Japanese manga, and anime. You answer in a very comprehensive and precise manner in English."
    else:
        system_prompt = "Tu es Animetix, un expert absolu de la culture otaku, des mangas et des anime japonais. Tu reponds de maniere tres complete et precise en francais."

    messages = [{"role": "system", "content": system_prompt}]

    if "turns" in item and item["turns"]:
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

    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    return {"text": formatted}


train_dataset = train_dataset.map(
    process_chatml, remove_columns=train_dataset.column_names
)
eval_dataset = eval_dataset.map(
    process_chatml, remove_columns=eval_dataset.column_names
)
print("Dataset preprocessing complete.")

# 4. BitsAndBytes Config (4-bit QLoRA)
print("Preparing BitsAndBytes double-quantization configuration...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

# 5. Training config setup
print("Initializing SFTConfig...")
config = SFTConfig(
    output_dir="otaku-qwen-7b-adapter",
    push_to_hub=True,
    hub_model_id="MissawB/otaku-qwen-7b-adapter",
    hub_strategy="every_save",
    num_train_epochs=1,
    max_steps=100,  # Fast run to update weights
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=10,
    save_strategy="steps",
    save_steps=50,
    save_total_limit=1,
    eval_strategy="steps",
    eval_steps=50,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    report_to="trackio",
    project="animetix-expert",
    run_name="qwen35-9b-star-lora",
)

# 6. LoRA adapter setup
print("Initializing LoraConfig...")
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
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

# 7. Initialize Trainer
print("Initializing SFTTrainer...")
trainer = SFTTrainer(
    model=model_id,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    args=config,
    model_init_kwargs={
        "quantization_config": bnb_config,
        "torch_dtype": torch.float16,
        "trust_remote_code": True,
    },
)

# 8. Train & Push
print("Starting training loop...")
trainer.train()

print("Saving final LoRA adapter & pushing to Hugging Face Hub...")
trainer.push_to_hub()

print("Finished! Closing Trackio tracker...")
trackio.finish()

print("Fine-tuning job successfully completed!")
