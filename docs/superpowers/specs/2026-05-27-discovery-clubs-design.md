# 👥 Design Spec: Animetix Discovery Clubs (Phase 4)

**Date:** 2026-05-27  
**Status:** Approved  
**Topic:** User-created clubs with collaborative challenges and live events.  
**Roadmap Context:** Phase 4 of the "Expansion of Animetix" (Social & Community).

---

## 1. Executive Summary
**Discovery Clubs** are the social cornerstone of Animetix. They allow users to form interest-based communities, participate in synchronized live events like "The Grand Blindtest", and compete in internal leaderboards. Premium users gain the exclusive ability to found and manage these clubs, creating a strong incentive for subscription while driving platform-wide engagement.

---

## 2. Club Structure & Management

### 2.1 Creation & Tiers
- **Club Founding:** Restricted to **Premium** users. Founders can set the club's name, theme, and privacy (Public, Invite-Only, Private).
- **Membership Limits:**
    - **Free Users:** Can join up to 3 clubs.
    - **Premium Users:** Unlimited club memberships.

### 2.2 Roles
- **Founder:** Full administrative rights, can delete the club.
- **Officer:** Can accept new members and schedule events.
- **Member:** Can participate in chat and events.

---

## 3. Collaborative Features (Activities)

### 3.1 The "Grand Blindtest" Live
- **Mechanic:** A weekly synchronized music quiz where all connected members hear the same snippet and race to identify the anime/manga.
- **Scheduling:** Scheduled by club admins via the **Club Event Calendar**.
- **Tech:** Uses **Django Channels (WebSockets)** for real-time synchronization.

### 3.2 Internal Leaderboards
- Every club has its own leaderboard based on activity points (Blindtest wins, shared fusions, comments).
- Monthly "Club Legends" are highlighted on the club's homepage.

### 3.3 Collaborative Lists
- Members can contribute to shared media lists. The AI Mentor of the club provides "Club Insights" (e.g., "This club seems to love Psychological Thrillers; have you tried [Media]?").

---

## 4. Technical Architecture

### 4.1 Data Models (Backend)
- `DiscoveryClub`: stores metadata, theme, and founder.
- `ClubMembership`: links users to clubs with a `role` field.
- `ClubEvent`: stores scheduled events (Blindtests, Raids).
- `ClubMessage`: persistent chat history (limited to 100 messages for free clubs).

### 4.2 Real-time Engine
- **WebSockets:** Dedicated consumer for club rooms.
- **Event Orchestration:** Celery tasks to trigger event start notifications and handle the transition from "Lobby" to "Live Game".

### 4.3 Frontend Components
- `ClubDashboard`: The central hub for a club.
- `LiveBlindtestRoom`: The interactive gaming interface.
- `ClubDiscovery`: A search and recommendation page to find new clubs to join.

---

## 5. Monetization Synergy
- **Creator Lock:** Club creation is the primary "Social" reason to upgrade to Premium.
- **Visual Prestige:** Premium clubs can unlock custom themes and animated banners.
- **Permanent History:** Only Premium clubs keep their chat and event history indefinitely.

---

## 6. Success Criteria
- **Social Stickiness:** 30% of active users join at least one club within the first month.
- **Event Participation:** Average of 5 members per live club event.
- **Premium Conversion:** 10% of new Premium upgrades citing "Club Creation" as a primary motivator.

---

## 7. Next Steps
- **Task 1:** Backend models and basic CRUD for Clubs.
- **Task 2:** WebSocket infrastructure for Club Chat and Events.
- **Task 3:** Frontend Club Dashboard and Discovery UI.
