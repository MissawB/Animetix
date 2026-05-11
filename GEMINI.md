# Gemini Project Instructions - Double Scenario Project

This file contains foundational mandates for Gemini CLI interventions in this workspace. These instructions take absolute precedence over general defaults.

## Architectural Mandate: Hexagonal Architecture (Ports and Adapters)
The project MUST follow Hexagonal Architecture principles to ensure decoupling between core logic and infrastructure.

- **Domain (Core):** Pure business logic, entities, and use cases. No dependencies on external frameworks, databases (SQLite/Neo4j), or Dagster.
- **Ports (Interfaces):** Abstract definitions of required external capabilities (e.g., `UserRepository`, `InferenceService`).
- **Adapters (Infrastructure):** Concrete implementations of ports. 
    - **Driving Adapters:** CLI, Dagster Ops/Assets, API controllers.
    - **Driven Adapters:** Database clients (Neo4j, SQLite, ChromaDB), external API clients (Jikan).

## Coding Standards
- **Language:** Python 3.10+
- **Typing:** Mandatory strict type annotations for all function signatures and class members.
- **Testing:** Use `pytest` for all unit and integration tests.
- **Docstrings:** Use Google-style docstrings for all public modules, classes, and methods.
- **Linting:** Adhere to PEP 8 standards. Use `ruff` or `flake8` if available in the environment for validation.

## Workspace Specifics
- **Pipeline:** The `pipeline/` directory must strictly follow Dagster's functional patterns (Assets, Resources, and IO Managers).
- **Backend:** The `backend/` directory contains the Django-based service. Ensure clear separation between Django models (Adapters) and Domain entities.
- **Data & MLOps:** 
    - **Tracking:** ALWAYS use `trackio` for monitoring training jobs.
    - **Persistence:** Models MUST be pushed to the Hugging Face Hub (`push_to_hub=True`).
    - **Remote Training:** Prefer Hugging Face Jobs (`hf_jobs()`) for intensive training tasks.
    - **Efficiency:** Use `unsloth` for LoRA/QLoRA training whenever possible.
    - **RLHF/DPO:** Actively use user feedback for alignment using DPO trainers.

## Intervention Workflow
1. **Research:** Map changes to Domain, Port, or Adapter layers.
2. **Strategy:** Explain how the change preserves the Hexagonal integrity.
3. **Execution:** Implement logic in the correct layer.
4. **Validation:** Run `pytest` and verify architectural boundaries are not breached.
