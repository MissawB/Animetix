import os
import time
import argparse
from animetix.containers import get_container

def test_lora_hot_swapping():
    """
    Test de performance du Multi-LoRA Hot-Swapping.
    Mesure le temps nécessaire pour passer d'un contexte d'expertise à un autre
    sur le même modèle de base.
    """
    print("🚀 Starting Multi-LoRA Hot-Swapping Benchmark...")
    
    # Initialisation du service (qui charge le LocalLlamaAdapter avec le LoraManager)
    container = get_container()
    local_adapter = container.inference_engine().adapters[-1] # Récupère le LocalLlamaAdapter
    
    if not hasattr(local_adapter, 'lora_manager') or not local_adapter.lora_manager:
        print("❌ Error: MultiLoraManager not initialized on LocalLlamaAdapter.")
        return

    lora_manager = local_adapter.lora_manager
    
    # Chemins simulés vers des adaptateurs LoRA
    # Dans un vrai scénario, ces dossiers contiendraient les poids (adapter_model.safetensors)
    lora_shounen_path = "checkpoints/lora_expert_shounen"
    lora_shojo_path = "checkpoints/lora_expert_shojo"
    
    # On simule la présence des dossiers pour le test
    os.makedirs(lora_shounen_path, exist_ok=True)
    os.makedirs(lora_shojo_path, exist_ok=True)
    
    # 1. Chargement initial (peut prendre quelques secondes)
    print("\n⏳ Initializing adapters in memory...")
    start_load = time.time()
    lora_manager.load_adapter("shounen_expert", lora_shounen_path)
    lora_manager.load_adapter("shojo_expert", lora_shojo_path)
    print(f"✅ Adapters loaded in {(time.time() - start_load):.2f} seconds.")
    
    # 2. Benchmark du Hot-Swapping (Doit être en millisecondes)
    print("\n⚡ Benchmarking Hot-Swap latency...")
    swap_times = []
    
    for i in range(10):
        target = "shojo_expert" if i % 2 == 0 else "shounen_expert"
        
        start_swap = time.perf_counter()
        lora_manager.set_active_adapter(target)
        swap_duration = (time.perf_counter() - start_swap) * 1000 # en ms
        swap_times.append(swap_duration)
        
    avg_swap = sum(swap_times) / len(swap_times)
    
    print("\n" + "="*40)
    print(f"📊 HOT-SWAP PERFORMANCE")
    print(f"Total swaps performed: {len(swap_times)}")
    print(f"Average Swap Latency: {avg_swap:.2f} ms")
    if avg_swap < 50:
        print("🚀 Excellent! Sub-50ms latency allows real-time dynamic contexts.")
    else:
        print("⚠️ Warning: Swap latency is high. Check PEFT version or memory mapping.")
    print("="*40)

if __name__ == "__main__":
    test_lora_hot_swapping()
