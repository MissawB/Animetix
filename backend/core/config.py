from typing import Optional

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
