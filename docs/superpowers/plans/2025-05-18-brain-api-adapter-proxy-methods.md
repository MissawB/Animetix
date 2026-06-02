# BrainAPIAdapter Proxy Methods Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the implementation of `BrainAPIAdapter` by adding proxy methods for all remaining `InferencePort` abstract methods.

**Architecture:** Each method will follow a standardized proxy pattern: check for API URL, encode binary inputs to Base64, POST to a specific Brain API endpoint, and handle the response.

**Tech Stack:** Python, requests, base64.

---

### Task 1: Implement Image and Video Analysis Methods

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`

- [ ] **Step 1: Implement `classify_image`**
- [ ] **Step 2: Implement `get_video_temporal_embeddings`**
- [ ] **Step 3: Implement `localize_video_actions`**
- [ ] **Step 4: Implement `get_multimodal_late_interaction`**

### Task 2: Implement Generative and Transformative Methods

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`

- [ ] **Step 1: Implement `transform_image_to_anime`**
- [ ] **Step 2: Implement `transform_video_to_anime`**
- [ ] **Step 3: Implement `generate_soundscape`**
- [ ] **Step 4: Implement `generate_3d_scene`**
- [ ] **Step 5: Implement `generate_image`**

### Task 3: Implement Audio and Manga-specific Methods

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`

- [ ] **Step 1: Implement `clone_voice`**
- [ ] **Step 2: Implement `speech_to_speech`**
- [ ] **Step 3: Implement `inpaint_text_bubbles`**

### Task 4: Implement Diagnostic and Safety Methods

**Files:**
- Modify: `backend/adapters/inference/brain_api_adapter.py`

- [ ] **Step 1: Implement `get_diagnostics`**
- [ ] **Step 2: Implement `calculate_uncertainty`**
- [ ] **Step 3: Implement `moderate_content`**

### Task 5: Final Validation

- [ ] **Step 1: Verify all methods are implemented**
- [ ] **Step 2: Check for syntax errors and import consistency**
- [ ] **Step 3: Run a smoke test (if possible with dummy data)**
- [ ] **Step 4: Commit all changes**
