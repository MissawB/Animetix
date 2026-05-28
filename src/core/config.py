from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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
    
    model_config = SettingsConfigDict(env_file=".env")

# Initialisation globale
settings = Settings()
