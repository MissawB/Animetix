from abc import ABC, abstractmethod
from typing import Any


class VoiceProfileRepositoryPort(ABC):
    """Persistence port for voice profiles (keeps the ORM out of the domain)."""

    @abstractmethod
    def save_voice_sample(
        self,
        *,
        name: str,
        language: str,
        origin_detail: str,
        audio_bytes: bytes,
        definition: str = "",
        roles: str = "",
        impact: str = "Custom",
    ) -> Any:
        """Create or update a voice profile and store its WAV sample.

        Returns the persisted profile (an opaque object to the domain — the adapter
        owns its concrete type).
        """
