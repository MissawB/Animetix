"""Public domain exceptions.

The concrete exception hierarchy lives in
:mod:`core.domain.entities.exceptions`. This module is the stable public
import path used across the codebase (``from core.domain.exceptions import ...``)
and simply re-exports those classes.
"""

from .entities.exceptions import (
    AdapterLoadError,
    AgentLogicalFailure,
    AnimetixBaseError,
    AnimetixError,
    CatalogNotFoundError,
    ConfigurationError,
    ContentModerationError,
    DomainError,
    GameLogicError,
    ImageGenerationError,
    InferenceError,
    InferenceTimeoutError,
    InfrastructureError,
    KnowledgeGraphQueryError,
    MangaProcessingError,
    ParsingError,
    PromptTemplateError,
    QuotaExceededError,
    SearchIndexUnavailableError,
    SpatialComputingError,
    VideoProcessingError,
)

__all__ = [
    "AdapterLoadError",
    "AgentLogicalFailure",
    "AnimetixBaseError",
    "AnimetixError",
    "CatalogNotFoundError",
    "ConfigurationError",
    "ContentModerationError",
    "DomainError",
    "GameLogicError",
    "ImageGenerationError",
    "InferenceError",
    "InferenceTimeoutError",
    "InfrastructureError",
    "KnowledgeGraphQueryError",
    "MangaProcessingError",
    "ParsingError",
    "PromptTemplateError",
    "QuotaExceededError",
    "SearchIndexUnavailableError",
    "SpatialComputingError",
    "VideoProcessingError",
]
