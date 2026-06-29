import google.auth
from animetix_project.logging_config import get_logger
from django.conf import settings
from google.auth.transport.requests import AuthorizedSession

from .containers import get_container

logger = get_logger("animetix." + __name__)

# --- SETTINGS & CONSTANTS ---
DIFFICULTY_SETTINGS = {
    "Anime": {"Easy": 1000, "Normal": 500, "Hard": 200, "Impossible": 50},
    "Manga": {"Easy": 800, "Normal": 400, "Hard": 150, "Impossible": 30},
    "Character": {"Easy": 500, "Normal": 250, "Hard": 100, "Impossible": 20},
}

# For Akinetix-family modes where the PLAYER must recognise/guess the secret
# (Animinator, Qui est-ce?, and the Akinetix classic candidate pool). Rank
# ceiling into the popularity-sorted catalogue: Easy = only the most famous
# works, Impossible = the whole catalogue (deep cuts). This is the intuitive
# direction (Facile = très connus, Impossible = pépites obscures).
AKINETIX_DIFFICULTY_RANK = {
    "Easy": 150,
    "Normal": 500,
    "Hard": 1200,
    "Impossible": 2000,
}

# Legacy bridges removed. Directly use the DI Container (get_container()) for all domain services.


def check_achievements(user, event_type, data):
    """
    Pont entre les modèles Django et le service de domaine des succès.
    Appelé lors d'une victoire ou d'une action significative pour vérifier les déblocages.
    """
    from core.domain.entities.achievement import GameEvent  # noqa: E402

    container = get_container()
    achievement_service = container.core.achievement_service()

    # Construction de l'événement de domaine
    event = GameEvent(
        user_id=user.id,
        game_mode=data.get("game_mode", "classic"),
        media_type=data.get("media_type", "Anime"),
        was_won=(event_type == "win"),
        is_daily=data.get("is_daily", False),
        is_ranked=data.get("is_ranked", False),
        attempts=data.get("attempts", 0),
        streak=user.profile.current_streak,
        total_wins=user.profile.total_wins,
        total_games=user.profile.total_games,
        item_rarity=data.get("item_rarity", "Common"),
    )

    # Délégation au service de domaine
    return achievement_service.check_and_unlock(event)


def shutdown_brain_service():
    """
    Shuts down the animetix-brain Cloud Run GPU service by setting maxInstanceCount to 0.
    """
    project_id = getattr(settings, "GCP_PROJECT_ID", "animetix")
    service_name = getattr(settings, "GCP_BRAIN_SERVICE_NAME", "animetix-brain")
    region = getattr(settings, "GCP_BRAIN_REGION", "europe-west1")

    logger.info(
        f"Initiating programmatic shutdown for Cloud Run service {service_name} in {region}..."
    )

    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        session = AuthorizedSession(credentials)

        url = f"https://{region}-run.googleapis.com/v2/projects/{project_id}/locations/{region}/services/{service_name}"
        params = {"updateMask": "template.scaling.maxInstanceCount"}
        data = {"template": {"scaling": {"maxInstanceCount": 0}}}

        response = session.patch(url, params=params, json=data)
        if response.status_code == 200:
            logger.info(
                f"Successfully scaled service {service_name} to 0 instances. Budget Cap enforced."
            )
            return True, response.json()
        else:
            error_detail = response.text
            logger.error(
                f"Failed to shutdown Cloud Run service. Status code: {response.status_code}. Response: {error_detail}"
            )
            return False, error_detail

    except Exception as e:
        logger.exception(
            f"Error during programmatic shutdown of service {service_name}: {e}"
        )
        return False, str(e)


def restore_brain_service(max_instances=3):
    """
    Restores the animetix-brain Cloud Run GPU service by resetting maxInstanceCount to a positive value.
    """
    project_id = getattr(settings, "GCP_PROJECT_ID", "animetix")
    service_name = getattr(settings, "GCP_BRAIN_SERVICE_NAME", "animetix-brain")
    region = getattr(settings, "GCP_BRAIN_REGION", "europe-west1")

    logger.info(
        f"Restoring Cloud Run service {service_name} to maxInstanceCount={max_instances}..."
    )

    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        session = AuthorizedSession(credentials)

        url = f"https://{region}-run.googleapis.com/v2/projects/{project_id}/locations/{region}/services/{service_name}"
        params = {"updateMask": "template.scaling.maxInstanceCount"}
        data = {"template": {"scaling": {"maxInstanceCount": max_instances}}}

        response = session.patch(url, params=params, json=data)
        if response.status_code == 200:
            logger.info(
                f"Successfully restored service {service_name} to {max_instances} instances."
            )
            return True, response.json()
        else:
            error_detail = response.text
            logger.error(
                f"Failed to restore Cloud Run service. Status: {response.status_code}. Response: {error_detail}"
            )
            return False, error_detail

    except Exception as e:
        logger.exception(f"Error during restoration of service {service_name}: {e}")
        return False, str(e)
