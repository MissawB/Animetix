class AnimetixError(Exception):
    """Base class for all project-specific errors."""
    pass

class DomainError(AnimetixError):
    """Errors occurring within the domain logic."""
    pass

class InfrastructureError(AnimetixError):
    """Errors occurring in external systems (LLM, DB, API)."""
    pass

class InferenceError(InfrastructureError):
    """Raised when an AI model or inference engine fails."""
    pass

class ContentModerationError(InfrastructureError):
    """Raised specifically when moderation fails to run."""
    pass

class ParsingError(DomainError):
    """Raised when JSON or AI-generated data fails to parse/validate."""
    pass

class CatalogNotFoundError(DomainError):
    """Raised when an item is not found in the catalog."""
    pass

class GameLogicError(DomainError):
    """Raised when a game-specific rule is violated."""
    pass
