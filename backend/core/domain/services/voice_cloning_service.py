from ...ports.inference_port import InferencePort


class VoiceCloningService:
    def __init__(self, inference_port: InferencePort):
        self.inference_port = inference_port

    def clone(
        self,
        reference_audio: bytes,
        target_text: str,
        pitch: int = 0,
        model: str = "rvc_v2",
        index_rate: float = 0.75,
    ) -> bytes:
        # In a real RVC implementation, pitch and model would be passed to clone_voice.
        # For now, we follow the InferencePort signature and assume adapter handles params via context or internal logic.
        return self.inference_port.clone_voice(
            text=target_text, reference_audio=reference_audio, language="fr"
        )
