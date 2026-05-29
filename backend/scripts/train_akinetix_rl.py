import os
import argparse
import torch
import numpy as np
import sys

# Setup environment for Django-related imports
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"RL Training encountered an error: {e}")

from datasets import load_dataset
from trl import DPOTrainer, DPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from animetix.containers import get_container

def run_rl_training_simulation(episodes: int = 100):
    """
    Simulation d'un entraînement RL (Q-Learning simplifié) pour Akinetix.
    L'agent apprend à choisir les attributs qui réduisent le plus l'entropie.
    """
    print("🤖 Initializing Akinetix RL Environment...")
    container = get_container()
    rl_service = container.akinetix_rl_env_service()
    env = rl_service.create_env("Anime")
    
    # Simple Q-Table mapping State -> Action values
    # In reality, state is continuous (entropy), so we'd use DQN/PPO.
    # Here we mock a learning loop.
    
    print(f"📊 Action Space Size: {len(env.attributes)} attributes")
    print(f"🚀 Starting training loop for {episodes} episodes...")
    
    wins = 0
    total_steps = 0
    
    for episode in range(episodes):
        state, info = env.reset()
        done = False
        truncated = False
        episode_reward = 0
        
        while not (done or truncated):
            # Politique e-greedy simulée : on choisit une action (attribut à deviner)
            action = np.random.randint(0, len(env.attributes))
            
            next_state, reward, done, truncated, step_info = env.step(action)
            episode_reward += reward
            
            state = next_state
            
        if reward > 0:
            wins += 1
        total_steps += env.steps
            
        if (episode + 1) % 10 == 0:
            print(f"Episode {episode + 1}/{episodes} | Avg Steps: {env.steps} | Reward: {episode_reward:.2f}")

    print("\n" + "="*40)
    print("📈 TRAINING COMPLETED")
    print(f"Win Rate: {(wins/episodes)*100:.2f}%")
    print(f"Average steps per game: {total_steps/episodes:.2f}")
    print("="*40)

def train_dpo(model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct", dataset_path: str = "data/mlops/datasets/dpo_train_swarm.jsonl"):
    """
    Exécute le fine-tuning DPO (Direct Preference Optimization) pour le SLM local.
    Utilise le dataset généré par le loop Swarm-to-DPO.
    """
    print(f"🎯 Starting DPO Fine-tuning on {model_id}...")
    
    # Resolve absolute path for dataset
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_dataset_path = os.path.join(base_dir, dataset_path)
    
    if not os.path.exists(abs_dataset_path):
        print(f"❌ Dataset not found at {abs_dataset_path}")
        return

    # Load dataset
    dataset = load_dataset("json", data_files=abs_dataset_path, split="train")
    print(f"📊 Dataset loaded: {len(dataset)} preference pairs")

    # Device configuration
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"💻 Using device: {device}")

    # Quantization config (only for CUDA)
    bnb_config = None
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    # Load model and tokenizer
    print(f"📦 Loading model {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )
    
    if device == "cuda":
        model = prepare_model_for_kbit_training(model)

    # LoRA config
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Output directory
    output_dir = os.path.join(base_dir, "checkpoints", "akinetix_dpo_adapter")
    os.makedirs(output_dir, exist_ok=True)

    # Training arguments
    training_args = DPOConfig(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=5e-5,
        logging_steps=10,
        num_train_epochs=3,
        save_steps=50,
        lr_scheduler_type="cosine",
        optim="paged_adamw_32bit" if device == "cuda" else "adamw_torch",
        remove_unused_columns=False,
        run_name="akinetix-dpo-swarm",
        max_prompt_length=512,
        max_length=1024,
        fp16=True if device == "cuda" else False,
        report_to="none"
    )

    # Initialize DPOTrainer
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        beta=0.1,  # Temperature coefficient for DPO
    )

    # Start training
    print("🚀 Training started...")
    trainer.train()

    # Save final model
    final_output_path = os.path.join(base_dir, "checkpoints", "akinetix_dpo_final")
    trainer.save_model(final_output_path)
    print(f"✅ DPO Training complete. Adapter saved to {final_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=["rl-sim", "dpo"], default="rl-sim", help="Training mode")
    parser.add_argument("--episodes", type=int, default=100, help="Number of episodes for RL sim")
    parser.add_argument("--model", type=str, default="HuggingFaceTB/SmolLM2-135M-Instruct", help="Model ID for DPO")
    parser.add_argument("--dataset", type=str, default="data/mlops/datasets/dpo_train_swarm.jsonl", help="Dataset path for DPO")
    args = parser.parse_args()
    
    if args.mode == "rl-sim":
        run_rl_training_simulation(episodes=args.episodes)
    elif args.mode == "dpo":
        train_dpo(model_id=args.model, dataset_path=args.dataset)
