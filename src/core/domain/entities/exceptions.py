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

# Compatibility layer for existing code (will be deprecated)
AnimetixError = AnimetixBaseError
