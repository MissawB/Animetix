# /// script
# dependencies = [
#   "trl>=0.12.0",
#   "peft>=0.7.0",
#   "transformers>=4.45.0",
#   "unsloth",
#   "trackio",
#   "datasets",
#   "torch",
# ]
# ///

import logging
import os

from datasets import load_dataset
from trl import SFTConfig, SFTTrainer
from unsloth import FastLanguageModel

# Configuration du logger
logger = logging.getLogger("animetix." + __name__)


def train():
    # SOTA pour le raisonnement logique et la culture otaku (Juin 2026)
    model_name = "unsloth/Qwen3.5-9B"
    max_seq_length = 2048
    load_in_4bit = True

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        load_in_4bit=load_in_4bit,
        revision="main",
    )  # nosec B615

    # 2. Ajout de LoRA adapters avec Unsloth (2x plus rapide)
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
        lora_alpha=16,
        lora_dropout=0,  # Optimisé pour Unsloth
        bias="none",
        use_gradient_checkpointing="unsloth",  # 0 VRAM supplémentaire
        random_state=3407,
    )

    # 3. Préparation du Dataset
    # Pour un job distant, on charge soit depuis le Hub, soit on le génère/télécharge
    # Ici on suppose que le dataset a été uploadé sur le Hub ou on utilise un placeholder
    dataset_name = os.getenv("DATASET_NAME", "trl-lib/Capybara")  # Valeur par défaut
    dataset = load_dataset(dataset_name, split="train", revision="main")  # nosec B615

    # 4. Configuration de l'entraînement avec SFTConfig
    training_args = SFTConfig(
        output_dir="otaku-expert-adapter",
        max_seq_length=max_seq_length,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        # MLOps Mandates
        report_to="trackio",
        push_to_hub=True,
        hub_model_id=os.getenv(
            "HUB_MODEL_ID", "username/otaku-expert-qwen3-8b-adapter"
        ),
        # Trackio specifics
        project="DoubleScenario",
        run_name="expert_sft_unsloth_qwen3_8b",
    )

    # 5. Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",  # À adapter selon le dataset
        args=training_args,
    )

    # 6. Exécution
    trainer.train()

    # 7. Sauvegarde finale
    trainer.push_to_hub()
    logger.info("🚀 Training complete and pushed to Hub!")


if __name__ == "__main__":
    train()
