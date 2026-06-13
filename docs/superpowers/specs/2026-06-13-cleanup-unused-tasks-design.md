# Design Spec: Cleanup of Legacy and Redundant Tasks

Remove dead task files and consolidate duplicate task implementations in `backend/api/animetix/tasks/`.

## User Review Required

None.

## Proposed Changes

We are focusing on cleaning up `backend/api/animetix/tasks/` by removing duplicate files and ensuring that only the correct and most robust task definitions are used.

### Backend Tasks Component

#### [MODIFY] [__init__.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/tasks/__init__.py)
- Replace the simple wrapper implementation of `trigger_club_event` with the more robust code from the redundant `club_events.py` file, incorporating proper error handling and logging.

#### [DELETE] [fusion_tasks.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/tasks/fusion_tasks.py)
- Completely delete this file since its legacy tasks (`legacy_generate_fusion_scenario_task` and `legacy_generate_fusion_image_task`) are duplicate code and the active versions are already implemented in `__init__.py`.

#### [DELETE] [club_events.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix/tasks/club_events.py)
- Delete this file since its single task `trigger_club_event` has been fully merged into `__init__.py`.

## Verification Plan

### Automated Tests
- Run backend tests to verify that task registration and task modules load correctly:
  ```bash
  pytest tests/
  ```
