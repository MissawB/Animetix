import os
import torch
import json
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import Dataset

logger = logging.getLogger("animetix.pipeline." + __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_cpt(draft_model_id="checkpoints/animetix-draft-135m", limit=5000):
    """
    Continuous Pre-Training (CPT) sur le modèle Draft (135M).
    Entraîne le modèle à prédire le token suivant sur les synopsis purs pour injecter de nouvelles connaissances.
    """
    logger.info(f"🔄 Starting Continuous Pre-Training (CPT) on {draft_model_id}...")
    
    # 1. Préparation du Dataset de textes bruts (Synopsis)
    db_path = os.path.join(BASE_DIR, 'data', 'processed', 'clean_root_animes.json')
    if not os.path.exists(db_path):
        logger.error("❌ Anime DB not found.")
        return
        
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    texts = []
    for item in data[:limit]:
        desc = item.get('description', '')
        title = item.get('title', '')
        if desc and title:
            texts.append(f"Anime: {title}\nSynopsis: {desc}")
            
    if not texts:
        logger.error("❌ No text data found for CPT.")
        return
        
    dataset = Dataset.from_dict({"text": texts})
    
    # 2. Chargement du modèle et Tokenizer
    model_path = os.path.join(BASE_DIR, draft_model_id)
    if not os.path.exists(model_path):
        # Fallback au modèle de base si le draft n'a pas encore été distillé
        model_path = "HuggingFaceTB/SmolLM-135M"
        
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    # Important pour SmolLM/Llama
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    model = AutoModelForCausalLM.from_pretrained(model_path)
    
    # 3. Tokenisation
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=256)
        
    tokenized_datasets = dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    
    # Pour le Causal LM, les labels sont les input_ids
    def format_labels(examples):
        examples["labels"] = examples["input_ids"].copy()
        return examples
        
    tokenized_datasets = tokenized_datasets.map(format_labels, batched=True)
    
    # 4. Configuration de l'entraînement
    output_dir = os.path.join(BASE_DIR, "checkpoints", "animetix-draft-cpt-135m")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-5, # LR très faible pour le CPT pour ne pas détruire les connaissances existantes
        num_train_epochs=1,
        weight_decay=0.01,
        logging_steps=10,
        save_strategy="no", # CPT léger
        fp16=torch.cuda.is_available(),
        optim="adamw_torch"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
    )
    
    logger.info("🚀 Starting CPT Training...")
    try:
        trainer.train()
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        logger.info(f"✅ CPT Training Complete. Model saved to {output_dir}")
        return output_dir
    except Exception as e:
        logger.error(f"❌ CPT Training Failed: {e}")
        return None

if __name__ == "__main__":
    run_cpt()
