import os
import argparse
from backend.animetix.services import AnimetixService
import numpy as np

def run_rl_training_simulation(episodes: int = 100):
    """
    Simulation d'un entraînement RL (Q-Learning simplifié) pour Akinetix.
    L'agent apprend à choisir les attributs qui réduisent le plus l'entropie.
    """
    print("🤖 Initializing Akinetix RL Environment...")
    animetix = AnimetixService()
    rl_service = animetix.akinetix_rl_service
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
            # Dans la réalité, l'agent utiliserait le réseau de neurones
            action = np.random.randint(0, len(env.attributes))
            
            next_state, reward, done, truncated, step_info = env.step(action)
            episode_reward += reward
            
            # Apprentissage (mise à jour des poids) se ferait ici
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100)
    args = parser.parse_args()
    
    run_rl_training_simulation(episodes=args.episodes)
