# Design Specification: Backend Async Stream Inference

Adding asynchronous stream generation capabilities to the Animetix inference system to enable concurrent inference streams without blocking the main asyncio event loop.

## 1. Objectives & Context

Currently, the inference adapters and ports are fully synchronous. The `stream_generate()` method on `InferencePort` returns a synchronous generator, meaning any streaming request blocks the executing thread. This makes it impossible to parallelize multiple inference streams concurrently.

To support parallel generation streams (concurrency) in async routes and background tasks:
- We will add `astream_generate` to `InferencePort` returning an `AsyncGenerator[InferenceResponse, None]`.
- Provide a default, non-blocking asynchronous implementation in `InferencePort` that executes synchronous `stream_generate` in a thread pool executor and passes tokens through an `asyncio.Queue`.
- Implement native async HTTP streaming in `BrainAPIAdapter` using `httpx.AsyncClient`.
- Implement async routing and failover in `FallbackInferenceAdapter.astream_generate`.
- Expose `astream_generate` in `LLMService`.
- Add comprehensive automated tests to verify concurrency.

## 2. Proposed Changes

### 2.1 Core Ports

#### [InferencePort](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/ports/inference_port.py)
- Define a new async generator method `astream_generate` with a signature identical to `stream_generate`.
- Implement a thread-pool-based fallback that runs `stream_generate` inside `loop.run_in_executor(None, producer)` and yields tokens via an `asyncio.Queue`.

### 2.2 Adapters

#### [BrainAPIAdapter](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/brain_api_adapter.py)
- Override `astream_generate` to use `httpx.AsyncClient` and native async streaming context `async with client.stream(...)` to yield tokens without blocking.

#### [FallbackInferenceAdapter](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/fallback_adapter.py)
- Implement `astream_generate` to handle concurrent streaming routing and failovers asynchronously.
- Update `_build_capability_cache` to check for `astream_generate` and handle capability detection.

### 2.3 Core Domain Services

#### [LLMService](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/llm_service.py)
- Expose `astream_generate` which delegates directly to the underlying engine's `astream_generate`.

## 3. Verification Plan

### Automated Tests
- Create a new unit test suite in `tests/adapters/test_async_stream.py` to verify:
  - `InferencePort`'s default `astream_generate` correctly wraps synchronous generators asynchronously.
  - `BrainAPIAdapter`'s `astream_generate` correctly calls the backend API and yields stream chunks.
  - `FallbackInferenceAdapter`'s `astream_generate` handles failover and fallback correctly.
  - Multiple concurrent streams can be consumed in parallel using `asyncio.gather`.
- Run the tests:
  `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py`
