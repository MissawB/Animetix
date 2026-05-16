import logging
from core.domain.services.akinetix_rl_env import AkinetixRLEnvironment
from backend.animetix.models import GameplaySession
import numpy as np

logger = logging.getLogger("animetix.rl.selfplay")

class AkinetixSelfPlayCollector:
    """
    Collecteur de données de self-play. Joue des parties et enregistre
    les trajectoires (state, action, reward) en base pour le RL.
    """
    def __init__(self, catalog_db: list):
        self.env = AkinetixRLEnvironment(catalog_db)

    def run_episodes(self, n_episodes: int = 10):
        """Lance des épisodes et persiste les données de jeu."""
        logger.info(f"Starting self-play collection for {n_episodes} episodes...")
        for _ in range(n_episodes):
            state, info = self.env.reset()
            trajectory = []
            done = False
            
            while not done:
                # Politique aléatoire pour récolter de l'exploration (à remplacer par le modèle)
                action = np.random.randint(0, self.env.action_dim)
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                
                trajectory.append({
                    "state": state.tolist(),
                    "action": int(action),
                    "reward": float(reward)
                })
                state = next_state
                done = terminated or truncated
            
            # Persistance via Django Model
            GameplaySession.objects.create(
                game_mode="akinetix_rl_selfplay",
                media_type="Anime",
                target_item=info["target"],
                history=trajectory,
                was_won=True # Simplified for collection
            )
        logger.info("Self-play collection completed.")
