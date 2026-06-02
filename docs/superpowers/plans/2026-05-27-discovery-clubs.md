# 👥 Discovery Clubs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the "Discovery Clubs" system, enabling users to form communities, chat, and participate in synchronized group activities.

**Architecture:** New Django models for club management, a WebSocket layer using Django Channels for real-time interaction, and a dedicated React dashboard for club members.

**Tech Stack:** Django, Django Channels (WebSockets), Redis, React, Lucide React.

---

### Task 1: Backend Models & CRUD for Clubs

**Files:**
- Modify: `backend/api/animetix/models.py`
- Modify: `backend/api/animetix/serializers.py`
- Modify: `backend/api/animetix/api/social.py`
- Test: `tests/backend/api/test_clubs_crud.py`

- [ ] **Step 1: Define Club Models**
  Add `DiscoveryClub`, `ClubMembership`, and `ClubEvent` to `backend/api/animetix/models.py`.

- [ ] **Step 2: Create Serializers**
  Add `DiscoveryClubSerializer` and `ClubMembershipSerializer` to `backend/api/animetix/serializers.py`.

- [ ] **Step 3: Implement ViewSets**
  Add `ClubViewSet` to `backend/api/animetix/api/social.py` with actions for `join`, `leave`, and `list_members`.
  **Enforce Premium rule:** Check `request.user_tier` before allowing club creation.

- [ ] **Step 4: Run Migrations**
  `python backend/api/manage.py makemigrations animetix && python backend/api/manage.py migrate`

- [ ] **Step 5: Write Tests**
  Verify that only Premium users can create clubs and that Free users are limited to 3 memberships.

- [ ] **Step 6: Commit**

---

### Task 2: WebSocket Layer (Real-time Chat & Sync)

**Files:**
- Create: `backend/api/animetix/consumers/club_consumer.py`
- Modify: `backend/api/animetix/routing.py`
- Modify: `backend/api/animetix_project/asgi.py`

- [ ] **Step 1: Implement `ClubConsumer`**
  Handle `connect`, `disconnect`, and `receive` (for chat messages).

- [ ] **Step 2: Register Routing**
  Add `path('ws/club/<int:club_id>/', consumers.ClubConsumer.as_view())` to `backend/api/animetix/routing.py`.

- [ ] **Step 3: Commit**

---

### Task 3: Frontend Club Dashboard & Discovery

**Files:**
- Create: `frontend/backend/features/social/ClubDashboard.tsx`
- Create: `frontend/backend/features/social/ClubDiscoveryPage.tsx`
- Create: `frontend/backend/features/social/components/ClubChat.tsx`
- Modify: `frontend/backend/api.ts`

- [ ] **Step 1: Add Club API helpers**
  Implement `getClubs`, `joinClub`, `createClub` in `frontend/backend/api.ts`.

- [ ] **Step 2: Build `ClubDiscoveryPage`**
  Searchable list of public clubs with "Join" buttons.

- [ ] **Step 3: Build `ClubDashboard`**
  Layout showing club info, member list, and the `ClubChat` component.

- [ ] **Step 4: Implement `ClubChat`**
  Connect to the WebSocket endpoint and display messages in real-time.

- [ ] **Step 5: Commit**

---

### Task 4: The "Grand Blindtest" Sync Logic

**Files:**
- Create: `backend/api/animetix/tasks/club_events.py`
- Modify: `backend/api/animetix/consumers/club_consumer.py`
- Test: `tests/backend/tasks/test_blindtest_sync.py`

- [ ] **Step 1: Implement Event Trigger**
  Create a Celery task that signals all members of a club when a scheduled Blindtest starts.

- [ ] **Step 2: Update Consumer for Event Sync**
  Add message types `event_start`, `next_question`, and `score_update` to the `ClubConsumer`.

- [ ] **Step 3: Commit**
