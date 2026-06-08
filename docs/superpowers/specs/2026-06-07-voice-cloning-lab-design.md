# Design Specification: Voice Cloning (RVC) Lab

Dedicated interface for zero-shot voice cloning using RVC (Retrieval-based Voice Conversion) technology.

## 1. Vision & Purpose
To provide users with a powerful workstation for synthesizing text into speech using their own voice or uploaded reference samples. This lab bridges the gap between high-level generative AI and precise audio manipulation.

## 2. User Interface (Pure SPA - React)

### Layout: Split Workspace (Workstation Style)
- **Left Column (Source Input):**
  - **Visualizer:** Real-time waveform display using Web Audio API (Canvas-based).
  - **Capture Controls:** Large "Record Mic" button (red/pulsing when active) and "Upload .WAV" secondary button.
  - **Parameters Panel:**
    - **Pitch Shift:** Slider for semi-tone adjustment (-12 to +12).
    - **Model Selection:** Dropdown for different RVC base models (v1, v2 40k, etc.).
    - **Index Rate:** Slider to control the influence of the reference timbre (0.0 to 1.0).
- **Right Column (Synthesis & Results):**
  - **Text Input:** Large textarea for the target message.
  - **Action Button:** "GENERATE CLONE" (gradient styling, high visual impact).
  - **Playback Card:** Result waveform, download button, and "Add to Collection" option.

### Visual Style
- **Aesthetic:** Cyberpunk/Omega Level (dark background, glowing red/cyan accents).
- **Feedback:** Haptic-like animations on record, pulsing glow during synthesis.

## 3. Technical Architecture

### Frontend
- **Page:** `frontend/src/pages/labs/VoiceLabPage.tsx`.
- **Routes:** Added to `LabRoutes.tsx` as `/lab/voice/`.
- **State Management:** `useVoiceCloning` hook leveraging `TanStack Query` for async processing.
- **Audio Processing:** `WaveformVisualizer` component using `requestAnimationFrame` and `AnalyserNode`.

### Backend (Django Headless)
- **Endpoint:** `POST /api/v1/labs/voice-cloning/`.
- **Payload:**
  ```json
  {
    "reference_audio": "base64_or_file",
    "target_text": "string",
    "params": {
      "pitch": 0,
      "model": "rvc_v2",
      "index_rate": 0.75
    }
  }
  ```
- **Service Layer:** `VoiceCloningService` in `backend/core/domain/services/`.
- **Adapter Layer:** Integration of `clone_voice` method in `AudioMixin` / `BrainAPIAdapter`.

## 4. Success Criteria
- [ ] User can record at least 5 seconds of audio and see a live waveform.
- [ ] User can upload a .wav file as a reference.
- [ ] Pitch adjustment accurately shifts the output tone.
- [ ] Synthesis returns a playable .wav file within 10-15 seconds (model dependent).

## 5. Security & Resource Management
- **Quotas:** Thinking budget (TTC) applied to voice cloning due to high GPU cost.
- **Privacy:** Reference audio samples are stored temporarily and encrypted at rest (Cloud KMS).
- **Validation:** Sanitize `target_text` to prevent prompt injection or TOS violations.

## 6. Self-Review Check
1. **Placeholder scan:** No TBDs. Parameters like pitch range and index rate are defined.
2. **Internal consistency:** Matches the "Workstation" choice from brainstorming. Hexagonal integrity maintained by placing logic in Domain Services.
3. **Scope check:** Focused strictly on Voice Cloning, not generic audio effects.
4. **Ambiguity check:** Clarified that the visualizer is frontend-side (Web Audio API) while cloning is backend-side (GPU).
