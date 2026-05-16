from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Configuration dynamique typée avec Pydantic."""
    
    # DB & Neo4j
    DATABASE_URL: str = "postgres://animetix:secretpassword@localhost:5432/animetix"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # Apps
    DJANGO_SECRET_KEY: str = "dev-secret-key"
    DJANGO_DEBUG: bool = False
    
    # AI/ML
    BRAIN_API_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env")

# Initialisation globale
settings = Settings()
