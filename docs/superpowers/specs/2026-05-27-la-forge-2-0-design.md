# 🎨 Design Spec: Animetix La Forge 2.0 (Mini-VN & Creator Mode)

**Date:** 2026-05-27  
**Status:** Approved  
**Topic:** Interactive Visual Novel generation and co-creation tools for fused universes.  
**Roadmap Context:** Phase 3 of the "Expansion of Animetix" (Monetization & Engagement).

---

## 1. Executive Summary
**La Forge 2.0** transforms static universe fusions into interactive experiences. It introduces a **Mini Visual Novel (VN)** format where users can play through short stories featuring their fused characters. Most importantly, it adds a **Director Mode** allowing users to co-create with the AI, editing dialogues and regenerating visuals to perfect their unique fan-fiction.

---

## 2. User Experience (UX)

### 2.1 The Mini-VN Player
- **Visuals:** High-quality anime sprites generated in real-time, overlaid on thematic backgrounds.
- **Interactivity:** Simple "click-to-advance" dialogue system with branching choices (Premium).
- **Audio:** Integration with existing `XTTSAdapter` for voice-over (Optional/Premium).

### 2.2 Director Mode (Creator Tool)
- **Timeline Editor:** A sidebar showing all scenes in the current story.
- **In-place Editing:** Clicking text bubbles allows manual correction of AI-generated dialogue.
- **AI Controls:**
    - **Regenerate Line:** Ask the LLM for a different take on a specific dialogue line.
    - **Regenerate Visual:** Re-roll the image generation for a character's expression or background.
- **Mood Selector:** Change character sprites based on emotional states (Happy, Angry, Stoic).

---

## 3. Technical Architecture

### 3.1 Script Generation Pipeline (Backend)
- **Role:** Orchestrates the narrative flow.
- **Process:**
    1. The LLM receives the two parent universes and the fusion metadata.
    2. It produces a **Story Script (JSON)**: `List[Scene(character, text, mood, bg_prompt)]`.
- **Consistency:** Uses a persistent `SessionSeed` to ensure character designs remain stable throughout the VN.

### 3.2 Real-time Visual Engine
- **Character Sprites:** Generated via `DiffusersAdapter` on transparent backgrounds.
- **Dynamic Backgrounds:** Generated based on the `bg_prompt` in the script.
- **Lazy Rendering:** Backgrounds for upcoming scenes are pre-rendered while the user is reading the current scene.

### 3.3 Persistence & Community
- **Database:** Fusions and their associated VN scripts are stored in PostgreSQL.
- **Asset Storage:** Generated images are stored in a cloud bucket with a 30-day retention policy (for free users) or permanent (for Premium).
- **Community Wall:** A gallery where users can publish and play each other's creations.

---

## 4. AI Orchestration & Quotas
- **Script Generation:** Consumes 1 major AI request from the user's daily quota.
- **Image Generation:** Each scene generation (character + background) counts as a high-tier unit.
- **Director Mode:** Manual text edits are free; AI-powered "Regenerations" consume remaining quota.

---

## 5. Success Criteria
- **UGC Volume:** At least 100 community-shared Visual Novels created in the first month.
- **Premium Upsell:** 15% increase in Premium conversions driven by the "Permanent Storage" and "Export to Video" features.
- **Visual Stability:** Character consistency rated >4/5 in automated aesthetic evaluations.

---

## 6. Next Steps
- **Task 1:** Domain logic for the VN Script Generator.
- **Task 2:** Sprite sterilization (transparent background) generation logic.
- **Task 3:** Frontend Director Mode UI with timeline.
