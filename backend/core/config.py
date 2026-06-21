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
