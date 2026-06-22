from typing import Any

from core.ports.voice_profile_port import VoiceProfileRepositoryPort


class DjangoVoiceProfileAdapter(VoiceProfileRepositoryPort):
    """Django ORM implementation of :class:`VoiceProfileRepositoryPort`."""

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
        from animetix.models import VoiceProfile
        from django.core.files.base import ContentFile
        from django.utils.text import slugify

        profile, _created = VoiceProfile.objects.update_or_create(
            name=name,
            defaults={
                "language": language,
                "origin": "youtube",
                "definition": definition or "Voix ingérée à la volée depuis YouTube.",
                "roles": roles or "Rôles personnalisés",
                "impact": impact or "Custom",
                "origin_detail": origin_detail,
            },
        )

        file_name = f"{slugify(name)}_sample.wav"
        profile.sample_file.save(file_name, ContentFile(audio_bytes), save=True)
        return profile
