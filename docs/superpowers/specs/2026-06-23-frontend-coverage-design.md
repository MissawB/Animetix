# Design Specification: Frontend Test Coverage Expansion

Implement unit tests for critical, uncovered frontend hooks that handle complex state, canvas/3D context, or real-time WebSockets to increase coverage metrics beyond the minimum thresholds.

## Targeted Hooks

1. `useTachideskExplorer.ts` (Explore/Suwayomi source/extension manager)
2. `useMultiverseCatalog.ts` (Multiverse catalog query, filter, pagination manager)
3. `useSocket.ts` (WebSocket hook for multiplayer room management)

---

## 1. useTachideskExplorer Hook Tests

### Location:
`frontend/src/pages/explore/tachidesk/hooks/__tests__/useTachideskExplorer.test.ts`

### Scope & Scenarios:
- **Mount & Initialization:**
  - Verify initial states: `activeTab` ('catalog'), loading states, sources, extensions, and error messages.
  - Verify that `fetchSources` is called asynchronously on mount (utilizing `queueMicrotask`).
- **Tab Swapping & Lifecycle:**
  - Verify switching to the 'extensions' tab triggers `fetchExtensions` and sets loading/extension states.
- **Search Flow:**
  - Verify `handleSearch` makes the correct API call with query params and handles success and failure cases.
- **Manga & Chapter Management:**
  - Verify `selectManga` gets favorite status and details.
  - Simulate chapter retrieval succeeding immediately.
  - Simulate chapter retrieval failing, triggering a manga import POST request, then retrying chapter retrieval.
- **Favorites Integration:**
  - Verify `toggleFavorite` sends correct POST requests and updates states.
  - Verify `updateFavoriteStatus` sends status updates and updates states.
- **Chapter Reading Flow:**
  - Verify `handleReadChapter` imports manga and calls `navigate` to the reader view.
- **Extensions Actions:**
  - Verify `handleExtensionAction` sends package actions, refreshes lists on success, and handles API errors.
- **Image Proxy URL:**
  - Verify `getProxiedImageUrl` encodes/proxies remote URLs or defaults appropriately.

---

## 2. useMultiverseCatalog Hook Tests

### Location:
`frontend/src/pages/labs/multiverse-catalog/hooks/__tests__/useMultiverseCatalog.test.ts`

### Scope & Scenarios:
- **State & Query Initialization:**
  - Verify query states with `@tanstack/react-query` using a custom wrapper.
  - Verify query param generation (`search`, `genre`, `sort`, `page`).
- **Debounced Search:**
  - Verify search query input changes are debounced by 350ms, resetting page number to 1.
- **Filter and Sorting Resets:**
  - Verify changes to sorting option or genre filters reset page number to 1.
- **Page Navigation Handlers:**
  - Verify pagination handlers (`handlePrevPage`, `handleNextPage`, `handleSelectPage`) modify page state correctly.
- **Filters Clearing:**
  - Verify `handleClearFilters` resets search, genre, sort, and page variables.

---

## 3. useSocket Hook Tests

### Location:
`frontend/src/hooks/__tests__/useSocket.test.ts`

### Scope & Scenarios:
- **WebSocket Connection Lifecycle:**
  - Verify that instantiating the hook creates a `WebSocket` connection with correct path construction (`ws/` or `wss/` relative to protocol/host).
  - Verify unmounting the hook calls the `close` method on the WebSocket instance with code `1000`.
- **Message and State Handling:**
  - Verify receiving a `game_state_update` message updates the state.
  - Verify receiving a `chat_message` appends to the chat log.
- **Message Sending & Queueing:**
  - Verify `sendAction` calls `send` directly when the connection is open.
  - Verify `sendAction` queues messages when the connection is closed or reconnecting.
  - Verify that once the connection opens, any queued messages are sent.
- **Reconnection Logic:**
  - Verify that when the WebSocket closes with a non-1000 code, it initiates reconnection.
  - Verify toast notifications are triggered during connection loss, reconnection attempts, and recovery.
  - Verify reconnection attempts are limited to `MAX_RECONNECT_ATTEMPTS` using exponential backoff.
