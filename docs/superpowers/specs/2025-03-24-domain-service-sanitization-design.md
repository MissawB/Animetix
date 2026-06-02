# Design Spec - Domain Service Sanitization (Phase 2)

## Overview
Refactor and consolidate domain services to ensure strict dependency injection, proper exception handling, and reduced redundancy in Akinetix-related services.

## Goals
1. **AgenticRAGService Sanitization**: 
   - Enforce DI (no default instantiations in `__init__`).
   - Use specific domain exceptions instead of `RuntimeError` or generic catches.
2. **Akinetix Services Consolidation**:
   - Merge `ClassicalAkinetixService` into `AkinetixService`.
   - Clean up `AkinetixRLService` and its environment.
3. **Container Update**:
   - Reflect all changes in `backend/api/animetix/containers.py`.

## Architecture

### 1. AgenticRAGService (backend/core/domain/services/agentic_rag_service.py)
- **DI**: The `__init__` will require all agents (planner, critic, etc.) to be passed. No `self.agent = agent or AgentClass(...)`.
- **Exceptions**: 
  - `except Exception` -> `except AnimetixError` (or more specific).
  - `except RuntimeError` -> `except InfrastructureError` or `except InferenceError`.
  - Specific check for `ParsingError` when handling LLM outputs.

### 2. Akinetix Services
- **backend/core/domain/services/akinetix_service.py**:
  - Rename `AkinetixDomainService` to `AkinetixService`.
  - Import and merge logic from `ClassicalAkinetixService`.
  - The `AkinetixService` will manage both the high-level game logic and the underlying probabilistic engine.
- **backend/core/domain/services/akinetix_rl_service.py**:
  - Rename `AkinetixRLDomainService` to `AkinetixRLService`.
  - Focus purely on RL-based decision making using `AkinetixRLEnvironment`.
- **backend/core/domain/services/akinetix_rl_env.py**:
  - Remove `AkinetixRLService` (class name collision and redundant).

### 3. Container (backend/api/animetix/containers.py)
- Update providers for:
  - `agentic_rag`: Explicitly inject all 12+ agents.
  - `akinetix_service`: Use the consolidated `AkinetixService`.
  - `akinetix_rl_service`: Use the renamed `AkinetixRLService`.
  - Add missing agent providers (Planner, Critic, etc.).

## Components

### AgenticRAGService
- Will be updated to be "purely" injected.
- Error handling will be more robust and specific to the domain.

### AkinetixService (Consolidated)
- Holds the `catalog_db`, `probs`, `asked_attributes`.
- Methods: `propose_next_question`, `update_probabilities`, `get_best_guess`.
- High-level methods: `start_new_game`, `process_answer`.

## Data Flow
1. **Container** instantiates all agents and services.
2. **AgenticRAGService** receives its full swarm of agents.
3. **AkinetixService** handles the classical game loop internally.

## Error Handling
- Use `InferenceError` for model failures.
- Use `InfrastructureError` for database/API failures.
- Use `ParsingError` for data validation failures.

## Testing Strategy
- Unit tests for `AgenticRAGService` with mocked agents.
- Unit tests for `AkinetixService` to ensure Bayes update logic still works after merger.
- Validation of container wiring.
