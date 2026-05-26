# 🤖 Design Spec: Animetix AI Companions (Phase 2)

**Date:** 2026-05-26  
**Status:** Approved  
**Topic:** Roster of Archetype Mentors acting as interactive platform guides.  
**Roadmap Context:** Phase 2 of the "Expansion of Animetix" (Monetization & Engagement).

---

## 1. Executive Summary
The **AI Companions** system introduces personified guides ("Mentors") that help users explore the Animetix platform. Each mentor has a distinct personality (Archetype) and specialization. They are accessible via a persistent floating overlay and react to the user's current context (visited pages, games played) using Animetix's RAG 2.0 engine.

---

## 2. Mentor Roster & Archetypes

### 2.1 Character Archetypes
- **The Sensei (Standard):** Wise, encouraging, expert in "Classic" and "Shonen" genres. (Free/Default).
- **The Tsundere (Unlockable):** Sharp-tongued but caring, fan of "Romance" and "Slice of Life". (Unlocked via 10 Akinetix Wins).
- **The Kuudere (Premium):** Stoic, analytical, provides data-driven recommendations and deep lore facts. (Premium Exclusive).

### 2.2 Acquisition Mechanics
- **Free Default:** One mentor is available to all users.
- **Progression-Based:** Users can unlock mentors by achieving specific milestones (Achievements).
- **Premium Access:** All mentors are immediately available to Premium users.

---

## 3. User Experience (UX)

### 3.1 The Companion Overlay
- A persistent, animated UI component in the bottom-right corner of the web application.
- **Visual Feedback:** The mentor's avatar changes expressions based on user interactions.

### 3.2 Interaction Modes
- **Passive Reactivity:** The mentor remains silent until clicked.
- **Contextual Inquiry:** Upon clicking, the user can ask "What do you think of this page?" or "Suggest me something similar".
- **Micro-Chat:** A small chat window allows for quick questions without navigating away from the current view.

---

## 4. Technical Architecture

### 4.1 Companion Service (Backend Domain Service)
- **Role:** Orchestrates the dialogue generation logic.
- **Personality Injection:** Uses `PromptManager` to wrap user queries with "System Instructions" specific to the active mentor.
- **Context Awareness:** Automatically receives the current URL/Media ID to enrich the RAG query.

### 4.2 Interaction Memory
- Stores the last 5-10 dialogue turns in a session-based cache (Redis) to maintain conversational flow.

### 4.3 API Endpoint
- `POST /api/v1/companion/interact/`
    - Payload: `{ mentor_id, user_message, context_url, history: [] }`
    - Response: `{ text_response, expression_id, quota_remaining }`

---

## 5. AI Integration & Guardrails
- **Prompting:** Uses specialized "Personality Templates" in `prompts.yaml`.
- **Quota Integration:** Every companion interaction counts as 1 "AI Request" against the user's daily quota.
- **Sanitization:** Responses are filtered for "In-Character" consistency and safety.

---

## 6. Success Criteria
- **Retention:** 20% increase in average session duration for users with an active mentor.
- **Discovery Rate:** Users clicking on mentor-suggested links at least twice per week.
- **Performance:** Response time < 2s for interactive chat.
