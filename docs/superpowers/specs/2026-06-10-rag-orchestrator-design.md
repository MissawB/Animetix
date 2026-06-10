# Design: Refactoring RAGWorkflowManager to Orchestrator Pattern

## Overview
This design refactors the monolithic `RAGWorkflowManager` into a decoupled orchestrator pattern with atomic state processors.

## Architectural Changes

### 1. `RAGOrchestrator`
- Replaces the monolithic `RAGWorkflowManager`.
- Acts as a lightweight state machine orchestrator.
- Manages the `RAGContext` and iterates through states.
- Does not contain specific agent logic; delegates to `StateProcessor` implementations.

### 2. `StateProcessor` (Base Class)
- Defines an interface for state processing.
- Method: `process(ctx: RAGContext) -> RAGState`

### 3. Concrete Processors
- `PlanProcessor`, `GraphExploreProcessor`, `ResearchProcessor`, etc.
- Each class encapsulates the specific `_handle_*` logic currently inside `RAGWorkflowManager`.

## Benefits
- **Maintainability:** Each state's logic is isolated in its own class.
- **Testability:** Processors can be unit-tested independently without mocking the entire manager.
- **Modularity:** Adheres to hexagonal architecture by separating orchestration from domain logic.
- **Scalability:** New states can be added by implementing a new `StateProcessor` without modifying the orchestrator.

## Migration Path
1. Create `StateProcessor` base class.
2. Implement concrete processors by moving logic from `RAGWorkflowManager._handle_*` methods.
3. Replace `RAGWorkflowManager` with `RAGOrchestrator` and a processor registry.
4. Update DI container to provide processors to the orchestrator.
