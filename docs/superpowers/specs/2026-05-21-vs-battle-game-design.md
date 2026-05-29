# Design Spec: VS Battle Game Engine (Multi-Agent Debate)

## 1. Overview
Implementation of a new game mode for the Animetix platform that simulates and judges combat between two characters using data from "Versus Battle" wikis (VS Battles Wiki, CSAP). The engine uses a multi-agent debate system to determine the winner based on factual evidence (AP, Speed, Hax, BIQ).

## 2. Architecture (Hexagonal)

### Domain Layer (Core)
- **Service:** `VsBattleService` in `backend/core/domain/services/creative/`.
- **Logic:**
    - Orchestrates the search for character data via `WebSearchPort`.
    - Triggers a multi-agent debate via `MultiAgentBus`.
    - Manages the state of the match (Character A, Character B, Debate history, Final Verdict).
- **Entities:** New `CombatCharacter` and `CombatResult` schemas in `backend/core/domain/entities/ai_schemas.py`.

### Ports Layer
- **WebSearchPort:** Used to fetch character profiles from Fandom API (VS Battles Wiki).
- **InferencePort:** Used for LLM generation of arguments and the final verdict.

### Adapter Layer
- **DuckDuckGoSearchAdapter/FandomAdapter:** Implementation for real-time wiki scraping.
- **MultiAgentBus:** Existing adapter for managing the debate between `Advocate_A`, `Advocate_B`, and `Judge`.

## 3. Debate Flow
1. **Search Phase:** System fetches full profiles for both characters, focusing on:
    - Attack Potency (Tiering)
    - Speed (Combat/Reaction)
    - Durability/Stamina
    - Abilities (Hax)
    - Intelligence/Skill (BIQ)
2. **Advocacy Phase:**
    - `Agent_A` presents the case for Character A's victory using specific "feats" and stats.
    - `Agent_B` presents the case for Character B, highlighting counters to Character A's powers.
3. **Rebuttal Phase:** Agents exchange brief arguments addressing the other's claims.
4. **Judgement Phase:** The `Judge` agent analyzes the arguments vs the raw stats and declares a winner with a detailed technical rationale.

## 4. Tone & Style
- **Primary:** Analytical & Evidence-based (Focus on Tiers and Feats).
- **Secondary:** Epic/Hype (To keep the user engaged during streaming).

## 5. UI/UX (Integration)
- New route `/game/vs-battle/`.
- Search interface for Character A and B.
- Streaming terminal view for the live debate.
- Visual card for the final winner with "Victory Reason" bullet points.

## 6. Testing Strategy
- **Unit Tests:** Mock wiki data and verify the `VsBattleService` correctly extracts tiers.
- **Integration Tests:** Verify `MultiAgentBus` correctly handles the combatant prompts.
- **Validation:** Use `Ragas` to evaluate the factual accuracy of the judge's verdict against the provided wiki context.
