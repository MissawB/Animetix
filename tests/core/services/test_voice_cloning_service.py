from unittest.mock import MagicMock

from backend.core.domain.services.voice_cloning_service import VoiceCloningService


def test_voice_cloning_service_calls_port():
    inference_port = MagicMock()
    service = VoiceCloningService(inference_port=inference_port)

    service.clone(
        reference_audio=b"fake_audio",
        target_text="Bonjour",
        pitch=2,
        model="rvc_v2",
        index_rate=0.5,
    )

    inference_port.clone_voice.assert_called_once_with(
        text="Bonjour",
        reference_audio=b"fake_audio",
        language="fr",  # Default logic
    )
