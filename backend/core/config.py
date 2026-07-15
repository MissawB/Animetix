from typing import Optional

from core.ports.config_port import ConfigPort, EnvConfig
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration dynamique typée avec Pydantic."""

    # DB & Neo4j
    DATABASE_URL: Optional[str] = None
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: Optional[str] = None

    # Apps
    DJANGO_SECRET_KEY: Optional[str] = None
    DJANGO_DEBUG: bool = False

    # AI/ML
    BRAIN_API_URL: Optional[str] = None

    # Tachidesk/Suwayomi
    SUWAYOMI_URL: str = "http://127.0.0.1:4567"
    SUWAYOMI_PASSWORD: Optional[str] = None

    # Google Cloud
    GCP_PROJECT_ID: str = "animetix-prod"
    GCP_LOCATION: str = "europe-west1"
    GCP_WORKFLOW_ID: str = "manga-voice-pipeline"
    GCS_MEDIA_BUCKET: str = "animetix-media-bucket"
    GCP_TASKS_QUEUE_NAME: str = "animetix-queue"
    GCP_TASKS_LOCATION: str = "europe-west1"
    GCP_TASKS_WORKER_URL: str = "https://missawb-animetix-web.hf.space/api/tasks/run/"
    GCP_TASKS_SERVICE_ACCOUNT: str = (
        "animetix-tasks-invoker@animetix.iam.gserviceaccount.com"
    )

    # Inference / Models
    CLIP_MODEL_NAME: str = "clip-ViT-B-32"
    IMAGEN_MODEL_NAME: str = "imagen-3.0-generate-001"
    MODEL_VERSION_TEXT: str = "v3"
    STRICT_MODEL_SECURITY: str = "true"
    STRICT_MODEL_VERIFICATION: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Initialisation globale
settings = Settings()


# --- Registre ConfigPort (accès aux settings du framework via port abstrait) ---
# Permet au code sans état injectable (fonctions au niveau module) d'accéder à la
# configuration applicative sans dépendre de Django. Par défaut on lit l'environnement ;
# l'adapter concret (DjangoConfigAdapter) est injecté une fois au boot via `configure()`
# (cf. AnimetixConfig.ready). Les services à classe privilégient l'injection constructeur.
_config_port: ConfigPort = EnvConfig()


def configure(adapter: ConfigPort) -> None:
    """Remplace l'implémentation de ConfigPort globale (appelé au démarrage)."""
    global _config_port
    _config_port = adapter


def get_config() -> ConfigPort:
    """Retourne l'implémentation de ConfigPort courante (repli : variables d'env)."""
    return _config_port
