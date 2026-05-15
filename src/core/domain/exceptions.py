class AnimetixError(Exception):
    """Base exception for all Animetix errors."""
    pass

class InferenceError(AnimetixError):
    """Raised when an AI inference call fails."""
    def __init__(self, message, provider=None, status_code=None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code

class CatalogError(AnimetixError):
    """Raised when a catalog operation fails."""
    pass

class CatalogNotFoundError(CatalogError):
    """Raised when a specific media catalog is not found."""
    def __init__(self, media_type):
        super().__init__(f"Catalog not found for media type: {media_type}")
        self.media_type = media_type

class GameLogicError(AnimetixError):
    """Raised when there is an error in game domain logic."""
    pass

class ValidationError(AnimetixError):
    """Raised when input validation fails at the domain level."""
    pass
