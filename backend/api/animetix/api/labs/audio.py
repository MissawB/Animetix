"""Audio labs: seiyuu discovery, voice ingestion/cloning, soundscape and S2S."""

from animetix_project.logging_config import get_logger

# Media-upload limits/MIME allow-lists are centralized in core.constants.
from core.constants import ALLOWED_AUDIO_MIMES  # noqa: E402
from core.utils.security import validate_file_mime_type, validate_file_size
from dependency_injector.wiring import Provide, inject  # noqa: E402
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...containers import Container  # noqa: E402

logger = get_logger("animetix." + __name__)

from core.domain.services.berrix_economy import FEATURE_BX_COSTS  # noqa: E402

from animetix.api.billing import deduct_berrix  # noqa: E402


class AudioLabDataView(APIView):
    """Metadata for the Audio Lab tools."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "active",
                "tools": [
                    {
                        "id": "soundscape",
                        "name": "Soundscape Generator",
                        "description": "Generate immersive ambient soundscapes for your video clips.",
                        "endpoint": "/api/v1/labs/audio/soundscape/",
                    },
                    {
                        "id": "s2s",
                        "name": "Voice Interaction (S2S)",
                        "description": "Direct speech-to-speech interaction with anime personas.",
                        "endpoint": "/api/v1/labs/audio/s2s/",
                    },
                    {
                        "id": "seiyuu-discovery",
                        "name": "Seiyuu Discovery",
                        "description": "Search and explore voice actors (seiyuu) and their iconic character roles.",
                        "endpoint": "/api/v1/labs/audio/seiyuu/",
                    },
                ],
            }
        )


class SeiyuuDiscoveryView(APIView):
    """Recherche et exploration des Seiyuu/Doubleurs et de leurs rôles."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "")
        language = request.query_params.get("language", "")
        origin = request.query_params.get("origin", "")

        from django.db.models import Q

        from animetix.models import VoiceProfile
        from animetix.serializers import VoiceProfileSerializer

        profiles = VoiceProfile.objects.all()

        if query:
            profiles = profiles.filter(
                Q(name__icontains=query)
                | Q(roles__icontains=query)
                | Q(definition__icontains=query)
            )

        if language:
            profiles = profiles.filter(language=language)
        if origin:
            profiles = profiles.filter(origin=origin)

        serializer = VoiceProfileSerializer(profiles, many=True)
        return Response({"query": query, "results": serializer.data})


class VoiceProfileIngestView(APIView):
    """Ingestion dynamique de voix à la volée depuis YouTube."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        voice_ingestion_service=Provide[Container.core.voice_ingestion_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.voice_ingestion_service = voice_ingestion_service

    def post(self, request):
        name = request.data.get("name")
        language = request.data.get("language", "japanese")
        youtube_url_or_query = request.data.get("youtube_url") or request.data.get(
            "query"
        )
        definition = request.data.get("definition", "")
        roles = request.data.get("roles", "")
        impact = request.data.get("impact", "Custom")

        if not name or not youtube_url_or_query:
            return Response(
                {"error": "Le nom et l'URL/requête YouTube sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Déduction des Berrix (30 Bx pour l'ingestion/découpage de voix)
        try:
            deduct_berrix(
                request.user,
                FEATURE_BX_COSTS["voice_ingest"],
                f"Ingestion vocale de {name}",
            )
        except Exception as e:
            return Response(
                {"error": f"Fonds insuffisants : {str(e)}"},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        from animetix.serializers import VoiceProfileSerializer

        try:
            profile = self.voice_ingestion_service.ingest_voice(
                name=name,
                language=language,
                youtube_url_or_query=youtube_url_or_query,
                definition=definition,
                roles=roles,
                impact=impact,
            )
            serializer = VoiceProfileSerializer(profile)
            return Response(
                {
                    "message": "Ingestion réussie !",
                    "profile": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("Erreur lors de l'ingestion vocale")
            return Response(
                {"error": "Erreur lors de l'ingestion"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SoundscapeGenerationView(APIView):
    """Génère un soundscape ambiant pour une vidéo."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        soundscape_service=Provide[Container.core.soundscape_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.soundscape_service = soundscape_service

    def post(self, request):
        video_file = request.FILES.get("video_file") or request.FILES.get("video")

        if not video_file:
            return Response({"error": "Video file is required."}, status=400)

        # Déduction des Berrix (50 Bx pour génération audio)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["soundscape"],
            "Génération de Soundscape Immersif",
        )

        try:
            video_bytes = video_file.read()
            result_url = self.soundscape_service.generate_soundscape_for_video(
                video_bytes
            )
            return Response({"status": "success", "audio_url": result_url})
        except Exception:
            logger.exception("Error in SoundscapeGenerationView")
            return Response({"error": "Internal server error"}, status=500)


class SpeechToSpeechLabView(APIView):
    """Interaction directe voix-à-voix (S2S)."""

    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        native_speech_llm_service=Provide[Container.core.native_speech_llm_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.native_speech_llm_service = native_speech_llm_service

    def post(self, request):
        audio_file = request.FILES.get("audio_file") or request.FILES.get("audio")
        persona = request.data.get("persona", "Standard")

        if not audio_file:
            return Response({"error": "Audio file is required."}, status=400)

        # Déduction des Berrix (10 Bx pour un tour de parole S2S)
        deduct_berrix(
            request.user,
            FEATURE_BX_COSTS["speech_to_speech"],
            f"Speech-to-Speech: {persona}",
        )

        try:
            audio_bytes = audio_file.read()
            result = self.native_speech_llm_service.process_voice_interaction(
                audio_bytes, persona=persona
            )

            if result.get("status") == "success":
                # Convert audio bytes to base64 for JSON transport
                import base64  # noqa: E402

                encoded_audio = base64.b64encode(result["audio_data"]).decode("utf-8")
                return Response({"status": "success", "audio_data": encoded_audio})
            return Response(result, status=400)
        except Exception:
            logger.exception("Error in SpeechToSpeechLabView")
            return Response({"error": "Internal server error"}, status=500)


class VoiceCloningLabView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @inject
    def __init__(
        self,
        voice_cloning_service=Provide[Container.core.voice_cloning_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.voice_cloning_service = voice_cloning_service

    def post(self, request):
        target_text = request.data.get("target_text")
        ref_audio_file = request.FILES.get("reference_audio")

        if not target_text or not ref_audio_file:
            return Response({"error": "Missing text or audio"}, status=400)

        # Déduction des Berrix (100 Bx pour clonage vocal multi-passes)
        deduct_berrix(
            request.user, FEATURE_BX_COSTS["voice_clone"], "Voice Cloning (Audio)"
        )

        # Validation: Pitch must be an integer
        try:
            pitch = int(request.data.get("pitch", 0))
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid pitch value. Must be an integer."}, status=400
            )

        # Validation: File size (Max 5MB as per review)
        MAX_VOICE_AUDIO_SIZE = 5 * 1024 * 1024
        if not validate_file_size(ref_audio_file.size, MAX_VOICE_AUDIO_SIZE):
            return Response(
                {"error": "Reference audio file too large (Max 5MB)."}, status=400
            )

        try:
            audio_bytes = ref_audio_file.read()

            # Validation: MIME Type
            if not validate_file_mime_type(audio_bytes, ALLOWED_AUDIO_MIMES):
                return Response(
                    {"error": "Invalid file type. Only wav and mp3 are allowed."},
                    status=400,
                )

            result_audio = self.voice_cloning_service.clone(
                reference_audio=audio_bytes, target_text=target_text, pitch=pitch
            )
            # Return as base64 for pure SPA handling
            import base64  # noqa: E402

            encoded = base64.b64encode(result_audio).decode("utf-8")
            return Response(
                {"status": "success", "audio_data": f"data:audio/wav;base64,{encoded}"}
            )
        except Exception:
            logger.exception("Voice Cloning Error")
            return Response({"error": "Internal server error"}, status=500)
