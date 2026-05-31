# Spec: World Boss UI (The Epic Raid)

## Overview
The World Boss feature introduces a massive, community-driven event where players collaborate to defeat a common enemy by solving difficult, anime-related trivia challenges. The interface adopts an "Epic Raid" (RPG/MMO) aesthetic to emphasize the scale and urgency of the event.

## 1. Architecture & Layout
*   **Route:** `/game/world-boss/`
*   **Theme:** Dark, intense colors (reds, oranges, deep blacks).
*   **Structure:**
    *   **Header:** Boss identity (Name, Avatar/Silhouette), current Phase (e.g., "Phase 2 - Enragé"), and a countdown timer indicating when the boss will escape.
    *   **Global Health Bar (The Raid):** A massive, central progress bar displaying `current_hp` vs `total_hp`. It updates in real-time via WebSockets. Visual markers on the bar indicate phase transition thresholds.
    *   **Combat Zone (Main Action):** The central area where the current hard-core trivia challenge is displayed.
    *   **Personal Contribution & Loot Tracker:** A side panel or dedicated section showing the user's total damage contributed and their current "Loot Tier" progression.
    *   **DPS Meter (Leaderboard):** A sidebar component showing the top 5 contributors to the current boss to foster competition.

## 2. Core Interactions & Data Flow
*   **Attacking the Boss:**
    *   Players are presented with difficult, AI-generated or curated trivia challenges.
    *   Submitting an answer triggers an API call (REST).
    *   **Success:** Triggers a "critical hit" animation (screen shake, damage numbers floating up). The boss's global HP decreases.
    *   **Failure:** Triggers a "block/parry" animation. No damage dealt.
    *   *Anti-cheat consideration:* A short timer (e.g., 60 seconds) per question to discourage searching for answers.
*   **Real-time Updates:**
    *   A WebSocket connection (reusing `NotificationConsumer` or a new `BossConsumer`) broadcasts HP updates and phase changes to all active players.
    *   Phase changes trigger global visual shifts (e.g., the background turns deeper red, animations become more aggressive).

## 3. Reward System (Loot Table)
*   **Mechanic:** Rewards are not guaranteed per hit, nor restricted only to the final kill. Instead, dealing damage increases the player's chance of receiving a drop.
*   **Loot Tiers:** As players deal damage, their personal "Loot Tier" increases (Common -> Rare -> Epic -> Legendary), improving their drop rates for better rewards.
*   **Drop Presentation:** When a loot drop occurs upon a successful hit, a "Gacha-style" animation (e.g., an opening chest) appears via a Toast or Modal, revealing the reward (XP, badges, creative fusions, etc.).
*   **Kill Reward:** Defeating the boss grants a guaranteed high-tier loot drop for all participants.

## 4. Components Breakdown (React)
*   `WorldBossPage`: Main container, manages WebSocket connection and overall state.
*   `BossHeader`: Displays boss info, phase, and timer.
*   `GlobalHealthBar`: Animated progress bar with phase markers.
*   `CombatTerminal`: Handles displaying the question, input field, timer, and submission logic.
*   `LootTracker`: Displays personal damage and current drop chance tier.
*   `RaidLeaderboard`: The "DPS Meter" for top contributors.
*   `DamageNumber`: Floating text component for visual feedback on hits.

## 5. Backend Integration Points
*   **Models:** Utilizes existing `GlobalBoss` and `BossParticipation`.
*   **API Endpoints:**
    *   `GET /api/v1/boss/active/`: Fetch current boss state and active challenge.
    *   `POST /api/v1/boss/attack/`: Submit challenge answer. Returns success/fail, damage dealt, and any loot dropped.
*   **WebSockets:** Broadcast events for `HP_UPDATE` and `PHASE_CHANGE`.

## 6. Open Questions / TBD
*   Exact calculation formula for Loot drop probabilities based on damage.
*   Structure of the trivia challenges (Text input vs. Multiple Choice) depending on what the backend currently generates for `community_hints`.