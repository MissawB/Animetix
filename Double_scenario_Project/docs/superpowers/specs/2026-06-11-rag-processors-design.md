# Design: RAG Processor Refactor

## Architecture
- Extract `_handle_research` and `_handle_acquire_knowledge` from `RAGWorkflowManager` into `ResearchProcessor` and `AcquireKnowledgeProcessor`.
- Inherit from `StateProcessor`.
- Update `StateProcessor` interface to return a generator of `StreamStep` dicts, returning a final `RAGState`.

## Data Flow
- `RAGWorkflowManager` will delegate to these processors.
- Processors will `yield` `StreamStep` dictionaries to the workflow manager.

## Testing
- Unit tests for both processors, mocking dependencies.
- Verify `StreamStep` yields and `RAGState` return.
