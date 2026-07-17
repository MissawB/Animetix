"""Real Kyutai STT + XTTS S2S cascade smoke test — brain/L4 only.

Skipped unless a CUDA GPU is present (never in CI or on the dev box).
Run on the brain: `pytest -m gpu tests/adapters/test_s2s_inference_gpu.py`.
"""

import io
import wave

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")

if not torch.cuda.is_available():
    pytest.skip("CUDA GPU required for S2S smoke test", allow_module_level=True)

pytestmark = pytest.mark.gpu


def _one_second_of_silence_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(np.zeros(24000, dtype=np.int16).tobytes())
    return buffer.getvalue()


def test_real_cascade_returns_wav():
    from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter

    engine = UnifiedInferenceAdapter()
    out = engine.speech_to_speech(
        _one_second_of_silence_wav(), system_prompt="Dis bonjour."
    )
    assert isinstance(out, bytes) and len(out) > 44
