# XTTSAdapter Audio Mocks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `generate_soundscape` and `speech_to_speech` in `XTTSAdapter` as graceful mocks to avoid `InferenceNotImplementedError`.

**Architecture:** Add methods to `XTTSAdapter` that return mock data (empty WAV for soundscape, passthrough for speech-to-speech) and log warnings.

**Tech Stack:** Python, wave, io, logging.

---

### Task 1: Create Unit Tests for Audio Mocks

**Files:**
- Create: `tests/adapters/test_xtts_adapter_audio.py`

- [ ] **Step 1: Write initial tests for missing methods**

```python
import pytest
import io
import wave
from backend.adapters.inference.xtts_adapter import XTTSAdapter

def test_generate_soundscape_mock():
    adapter = XTTSAdapter()
    res = adapter.generate_soundscape(prompt="birds in forest", duration=5)
    
    assert isinstance(res, bytes)
    assert len(res) > 44  # WAV header is at least 44 bytes
    
    # Verify it's a valid WAV header
    with io.BytesIO(res) as f:
        with wave.open(f, 'rb') as wav:
            assert wav.getnchannels() == 1
            assert wav.getsampwidth() == 2
            assert wav.getframerate() == 44100

def test_speech_to_speech_mock():
    adapter = XTTSAdapter()
    audio_data = b"original audio"
    target_voice = b"target voice"
    res = adapter.speech_to_speech(audio_data, target_voice)
    
    assert res == audio_data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/adapters/test_xtts_adapter_audio.py`
Expected: FAIL with `AttributeError: 'XTTSAdapter' object has no attribute 'generate_soundscape'`

- [ ] **Step 3: Commit**

```bash
git add tests/adapters/test_xtts_adapter_audio.py
git commit -m "test: add tests for XTTS audio mocks"
```

### Task 2: Implement `generate_soundscape`

**Files:**
- Modify: `backend/adapters/inference/xtts_adapter.py`

- [ ] **Step 1: Implement the method**

```python
    def generate_soundscape(self, prompt: str, duration: int = 10) -> bytes:
        """
        Génère une ambiance sonore (Mock).
        """
        import wave
        import io
        logger.warning("Mock implementation of generate_soundscape used")
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            # Empty audio data
            
        return buffer.getvalue()
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/adapters/test_xtts_adapter_audio.py::test_generate_soundscape_mock`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/xtts_adapter.py
git commit -m "feat: implement generate_soundscape mock in XTTSAdapter"
```

### Task 3: Implement `speech_to_speech`

**Files:**
- Modify: `backend/adapters/inference/xtts_adapter.py`

- [ ] **Step 1: Implement the method**

```python
    def speech_to_speech(self, audio_data: bytes, target_voice: bytes) -> bytes:
        """
        Interaction End-to-End Voice (Mock).
        """
        logger.warning("Mock implementation of speech_to_speech used")
        return audio_data
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/adapters/test_xtts_adapter_audio.py::test_speech_to_speech_mock`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/adapters/inference/xtts_adapter.py
git commit -m "feat: implement speech_to_speech mock in XTTSAdapter"
```
