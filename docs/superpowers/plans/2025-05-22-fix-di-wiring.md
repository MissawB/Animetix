# Fix Dependency Injection Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broken DI wiring in `backend/api/animetix/api` by updating `Provide[Container.X]` to `Provide[Container.subcontainer.X]`.

**Architecture:** Use the modularized `Container` structure where services are grouped into sub-containers: `infrastructure`, `persistence`, `inference`, `agentic`, and `core`.

**Tech Stack:** Python, Dependency Injector.

---

### Task 1: Update API Games Modules

**Files:**
- Modify: `backend/api/animetix/api/games/akinetix.py`
- Modify: `backend/api/animetix/api/games/akinetix_rl.py`
- Modify: `backend/api/animetix/api/games/archetypist.py`
- Modify: `backend/api/animetix/api/games/blindtest.py`
- Modify: `backend/api/animetix/api/games/classic.py`
- Modify: `backend/api/animetix/api/games/covertest.py`
- Modify: `backend/api/animetix/api/games/emoji.py`
- Modify: `backend/api/animetix/api/games/paradox.py`
- Modify: `backend/api/animetix/api/games/vision.py`

- [ ] **Step 1: Update akinetix.py**
    - `akinetix_service` -> `Container.core.akinetix_service`
    - `catalog_service` -> `Container.core.catalog_service`

- [ ] **Step 2: Update akinetix_rl.py**
    - `akinetix_expert_service` -> `Container.core.akinetix_expert_service`
    - `catalog_service` -> `Container.core.catalog_service`

- [ ] **Step 3: Update archetypist.py**
    - `catalog_service` -> `Container.core.catalog_service`

- [ ] **Step 4: Update blindtest.py**
    - `blind_test_service` -> `Container.core.blind_test_service`
    - `catalog_service` -> `Container.core.catalog_service`
    - `game_service` -> `Container.core.game_service`

- [ ] **Step 5: Update classic.py**
    - `catalog_service` -> `Container.core.catalog_service`
    - `game_service` -> `Container.core.game_service`

- [ ] **Step 6: Update covertest.py**
    - `cover_test_service` -> `Container.core.cover_test_service`
    - `catalog_service` -> `Container.core.catalog_service`
    - `game_service` -> `Container.core.game_service`

- [ ] **Step 7: Update emoji.py**
    - `catalog_service` -> `Container.core.catalog_service`
    - `emoji_service` -> `Container.core.emoji_service`
    - `game_service` -> `Container.core.game_service`

- [ ] **Step 8: Update paradox.py**
    - `catalog_service` -> `Container.core.catalog_service`
    - `paradox_service` -> `Container.core.paradox_service`

- [ ] **Step 9: Update vision.py**
    - `vision_quest_service` -> `Container.core.vision_quest_service`
    - `catalog_service` -> `Container.core.catalog_service`

- [ ] **Step 10: Commit Games API updates**

### Task 2: Update Top-Level API Modules

**Files:**
- Modify: `backend/api/animetix/api/companion.py`
- Modify: `backend/api/animetix/api/graph.py`
- Modify: `backend/api/animetix/api/mlops.py`
- Modify: `backend/api/animetix/api/labs.py` (Also fix manual container access)

- [ ] **Step 1: Update companion.py**
    - `companion_service` -> `Container.core.companion_service`
    - `usage_port` -> `Container.infrastructure.usage_port`

- [ ] **Step 2: Update graph.py**
    - `graph_persistence_port` -> `Container.persistence.graph_persistence_port`

- [ ] **Step 3: Update mlops.py**
    - `eval_adapter` -> `Container.persistence.eval_adapter`
    - `repository` -> `Container.persistence.repository`
    - `feedback_adapter` -> `Container.persistence.feedback_adapter`
    - `gold_dataset_adapter` -> `Container.persistence.gold_dataset_adapter`
    - `dpo_feedback_loop` -> `Container.core.dpo_feedback_loop`

- [ ] **Step 4: Update labs.py**
    - Update all `container.attribute` to `container.subcontainer.attribute`
    - `health_dashboard_service` -> `core.health_dashboard_service`
    - `graph_healer_service` -> `core.graph_healer_service` (Wait, need to check if it's there)
    - `drift_service` -> `core.drift_service`
    - `dpo_service` -> `core.dpo_feedback_loop` (Check naming)
    - `spatial_computing_service` -> `core.spatial_computing_service`
    - `manga_flow_service` -> `core.manga_flow_service`
    - `vision_service` -> `core.vision_service`
    - `voice_cloning_service` -> `core.voice_cloning_service`
    - `self_evolving_compiler` -> `core.self_evolving_compiler`
    - `synaptic_plasticity_simulator` -> `core.synaptic_plasticity_simulator`
    - `autonomous_domain_synthesizer` -> `core.autonomous_domain_synthesizer`

- [ ] **Step 5: Verify labs.py mappings**

- [ ] **Step 6: Commit Top-Level API updates**

### Task 3: Verification

- [ ] **Step 1: Run basic import check**
    - `python -c "from animetix.containers import Container; print('Container loaded OK')"`
- [ ] **Step 2: (Optional) Run Django setup check**
    - `python manage.py check` (if environment allows)
