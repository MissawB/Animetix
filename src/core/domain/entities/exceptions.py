class AnimetixBaseError(Exception):
    """Base class for all project-specific errors."""
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}

class DomainError(AnimetixBaseError):
    """Errors occurring within the domain logic."""
    pass

class InfrastructureError(AnimetixBaseError):
    """Errors occurring in external systems (LLM, DB, API)."""
    pass

class InferenceError(InfrastructureError):
    """Raised when an AI model or inference engine fails."""
    pass

class InferenceTimeoutError(InferenceError):
    """Raised when an AI model or inference engine times out."""
    pass

class QuotaExceededError(DomainError):
    """Raised when a user has reached their daily AI limit."""
    pass

class ContentModerationError(InfrastructureError):
    """Raised specifically when moderation fails to run."""
    pass

class ParsingError(DomainError):
    """Raised when JSON or AI-generated data fails to parse/validate."""
    pass

class PromptTemplateError(DomainError):
    """Raised when a prompt template is missing or malformed."""
    pass

class CatalogNotFoundError(DomainError):
    """Raised when an item is not found in the catalog."""
    pass

class GameLogicError(DomainError):
    """Raised when a game-specific rule is violated."""
    pass

class AgentLogicalFailure(DomainError):
    """Raised when an agent makes a logical error or reaches an inconsistent state."""
    pass

class KnowledgeGraphQueryError(InfrastructureError):
    """Raised when a query to the knowledge graph (Neo4j) fails."""
    pass

class SpatialComputingError(InferenceError):
    """Raised when depth estimation or 3D scene generation fails."""
    pass

class MangaProcessingError(InferenceError):
    """Raised when manga OCR, translation, or text inpainting fails."""
    pass

class VideoProcessingError(InferenceError):
    """Raised when video analysis, temporal embeddings, or action localization fails."""
    pass

class ImageGenerationError(InferenceError):
    """Raised when image generation or style transfer fails."""
    pass

class AdapterLoadError(InfrastructureError):
    """Raised when a model or adapter fails to load (e.g., missing weights, bad config)."""
    pass

# Compatibility layer for existing code (will be deprecated)
AnimetixError = AnimetixBaseError
