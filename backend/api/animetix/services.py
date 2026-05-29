from animetix_project.logging_config import get_logger
from .containers import get_container

logger = get_logger('animetix.' + __name__)

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    'Anime': {'Easy': 1000, 'Normal': 500, 'Hard': 200, 'Impossible': 50},
    'Manga': {'Easy': 800, 'Normal': 400, 'Hard': 150, 'Impossible': 30},
    'Character': {'Easy': 500, 'Normal': 250, 'Hard': 100, 'Impossible': 20}
}

# Legacy bridges removed. Directly use the DI Container (get_container()) for all domain services.
