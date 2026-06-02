# Design Doc: XTTSAdapter Audio Mock Implementation

**Date:** 2025-05-24
**Topic:** Implementation of missing Audio methods in XTTSAdapter as graceful mocks.

## 1. Context
The `XTTSAdapter` is used for voice cloning but currently lacks implementations for `generate_soundscape` and `speech_to_speech`, which are part of the broader `InferencePort` interface (though with slightly modified signatures for this specific adapter's current requirements). Implementing these as mocks avoids `InferenceNotImplementedError` and allows services to call these methods safely.

## 2. Requirements
- Add `generate_soundscape(prompt, duration)` returning empty WAV bytes.
- Add `speech_to_speech(audio_data, target_voice)` returning `audio_data`.
- Log warnings for both mock uses.
- Ensure no `InferenceNotImplementedError` is raised.

## 3. Architecture & Components
- **Adapter:** `backend/adapters/inference/xtts_adapter.py`
- **New Methods:**
    - `generate_soundscape(self, prompt: str, duration: int = 10) -> bytes`
    - `speech_to_speech(self, audio_data: bytes, target_voice: bytes) -> bytes`

## 4. Implementation Details

### 4.1. generate_soundscape
```python
def generate_soundscape(self, prompt: str, duration: int = 10) -> bytes:
    logger.warning("Mock implementation of generate_soundscape used")
    buffer = io.BytesIO()
    import wave
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        # Empty audio
    return buffer.getvalue()
```

### 4.2. speech_to_speech
```python
def speech_to_speech(self, audio_data: bytes, target_voice: bytes) -> bytes:
    logger.warning("Mock implementation of speech_to_speech used")
    return audio_data
```

## 5. Testing & Validation
- **Unit Test:** `tests/adapters/test_xtts_adapter_audio.py`
    - Test `generate_soundscape` returns bytes starting with `RIFF`.
    - Test `speech_to_speech` returns input bytes.
    - Verify logs contain warnings.
