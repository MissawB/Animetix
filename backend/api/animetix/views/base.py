from animetix_project.logging_config import get_logger

logger = get_logger("animetix." + __name__)

# Ne conserver que les constantes, logiques métiers internes ou fonctions non-HTML si nécessaires.
# Les fonctions de rendu de template comme index() et start_daily_challenge() sont intégralement supprimées.
