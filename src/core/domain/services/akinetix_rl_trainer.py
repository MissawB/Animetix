import logging
import numpy as np
from typing import Optional
import torch
import torch.nn as nn
import torch.optim as optim
from .akinetix_rl_env import AkinetixRLEnvironment

logger = logging.getLogger("animetix.rl")

class AkinetixPolicyNetwork(nn.Module):
    """Réseau de neurones simple pour la politique de sélection de questions Akinetix."""
    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        return self.net(x)

class AkinetixRLTrainer:
    """Service d'entraînement pour le mode Akinetix."""
    def __init__(self, env: AkinetixRLEnvironment):
        self.env = env
        self.state_dim = 3 # pool_size, entropy, steps
        self.action_dim = len(env.attributes)
        self.policy = AkinetixPolicyNetwork(self.state_dim, self.action_dim)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=1e-3)

    def train_step(self):
        """Exécute une itération d'entraînement (Policy Gradient)."""
        state, _ = self.env.reset()
        done = False
        saved_log_probs = []
        rewards = []

        while not done:
            state_tensor = torch.from_numpy(state).float()
            probs = self.policy(state_tensor)
            
            # Sélection d'action par échantillonnage
            action = torch.multinomial(probs, 1).item()
            saved_log_probs.append(torch.log(probs[action]))

            state, reward, terminated, truncated, _ = self.env.step(action)
            rewards.append(reward)
            done = terminated or truncated

        # Mise à jour simple (REINFORCE)
        loss = -torch.stack(saved_log_probs) * torch.tensor(rewards, dtype=torch.float32)
        self.optimizer.zero_grad()
        loss.sum().backward()
        self.optimizer.step()
        
        logger.info(f"Training step complete. Total reward: {sum(rewards):.2f}")
        return sum(rewards)
