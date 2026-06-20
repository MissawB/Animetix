# Task List (TODO) - Animetix

This document lists all the technical, architectural, and functional tasks remaining to be implemented or fixed. Completed tasks are archived in [docs/HISTORY.md](docs/HISTORY.md).

---

## 🚀 Expansion & Future
- [x] **Vocal Library & Seiyuu Integration:** Populate the database with voice actor/seiyuu profiles and wav samples, and integrate voice cloning/synthesis across Audio, Manga Voice, and Speech-to-Speech labs.
- [ ] **Compliance Reports:** Automate weekly security compliance reports.
- [x] **Offline Manga Library & Download Manager:** Create a dedicated page to manage local storage (IndexedDB via `idb-keyval`), list downloaded manga chapters, and read offline.
- [x] **Graph Repair Console (Graph Healer):** Develop an admin interface to audit Neo4j, merge duplicate entities, and heal structural relations via `GraphHealerService`.
- [x] **Plasticity Dashboard & Semantic Profile:** Design a dynamic user view displaying semantic weight evolution (Hebbian/STDP learning) and allowing configuration of cognitive plasticity and archetype drift. ✅ (2026-06-20)
- [x] **Berrix Economy Hub:** Integrate a wallet page (Cyber-Yen Wallet & Reward Center) to track the complete transaction ledger (credits/debits) of Berrix tokens (Bx) and manage active/passive attention mining.
- [x] **Tachidesk/Suwayomi Integration (Mihon Backend):** Connect the project to a local Tachidesk/Suwayomi instance to use Mihon/Tachiyomi extensions and access over 500 manga sources.
- [x] **Manga Reader Optimization (React UX):** Improve reading comfort in the frontend component (image preloading, infinite scroll for Webtoon mode, double-page split/fit, and reader configurations).
- [x] **Manga Extension Manager (Suwayomi):** Allow installing, uninstalling, and updating manga source extensions directly through the Animetix interface. ✅ (2026-06-20)
- [ ] **Manga Chapter Tracking & Notifications:** Check for updates of favorite mangas in the background via a Celery/Django periodic task and send WebSocket notifications when new chapters are released.
- [x] **Manga Reader Offline Mode (PWA):** Enable local downloading of chapters for offline reading via Service Workers and IndexedDB/Cache API.
- [ ] **Synchronize with Trackers (MAL / AniList):** Link users' third-party profiles to automatically synchronize their reading progress upon chapter completion.
- [ ] **Library Categorization & Sorting:** Organize the manga collection into custom folders ("Reading", "Completed", "Plan to Read") with filters and unread chapter counters.
- [x] **Real-time Club Chat:** Integrate an instant chat channel (via WebSockets / Django Channels) within each discovery Club to foster the community aspect.
- [x] **Self-Hosted AI Image Worker (MLOps):** Configure a local worker (Stable Diffusion / ComfyUI) managed by our task queue (`enqueue_task`) in case of budget overrun or unavailability of paid APIs, monitored on the "Cluster Health" dashboard.
- [x] **LLM Speed Optimization (Speculative Decoding & KV Cache):** Accelerate LLM response times by implementing speculative decoding (EAGLE, Medusa) and semantic caching/RadixAttention. *Note: Add the associated research papers in the dedicated page* [RESEARCH_PAPERS.md](file:///c:/Users/bahma/PycharmProjects/Projet solo/Double_scenario_Project/docs/RESEARCH_PAPERS.md).
---
*Last update: June 20, 2026*
