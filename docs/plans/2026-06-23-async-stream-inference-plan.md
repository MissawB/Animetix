# Backend Async Stream Inference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add asynchronous stream generation capabilities to the backend inference ports, adapters, and services to support concurrent, non-blocking generation streams.

**Architecture:** We introduce `astream_generate` in `InferencePort`. By default, it runs the blocking synchronous generator in a thread pool using `loop.run_in_executor` and yields tokens via an `asyncio.Queue`. We implement a native async HTTP stream using `httpx.AsyncClient` in `BrainAPIAdapter`, and implement asynchronous routing/failover in `FallbackInferenceAdapter`.

**Tech Stack:** Python 3.12, asyncio, httpx, pytest

---

## Proposed Changes

### Task 1: InferencePort Asynchronous Default Wrapper

**Files:**
- Modify: [inference_port.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/ports/inference_port.py)
- Test: [test_async_stream.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/adapters/test_async_stream.py) [NEW]

- [ ] **Step 1: Write the failing test**
  Create the test file `tests/adapters/test_async_stream.py` and write a test that verifies `InferencePort.astream_generate` wraps `stream_generate` using a thread pool.
  ```python
  import asyncio
  import pytest
  from core.ports.inference_port import InferencePort
  from core.domain.entities.ai_schemas import InferenceResponse

  class FakeSyncAdapter(InferencePort):
      def generate(self, prompt, system_prompt="sys", **kwargs):
          return InferenceResponse(text="sync")
      def get_text_embedding(self, text):
          return []
      def health_check(self):
          return {"status": "online"}
      def stream_generate(self, prompt, system_prompt="sys", **kwargs):
          yield InferenceResponse(text="chunk1")
          yield InferenceResponse(text="chunk2")

  @pytest.mark.asyncio
  async def test_inference_port_astream_generate_wraps_sync():
      adapter = FakeSyncAdapter()
      chunks = []
      async for chunk in adapter.astream_generate("Q"):
          chunks.append(chunk.text)
      assert chunks == ["chunk1", "chunk2"]
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_inference_port_astream_generate_wraps_sync -v`
  Expected: FAIL with `AttributeError: 'FakeSyncAdapter' object has no attribute 'astream_generate'`

- [ ] **Step 3: Write minimal implementation**
  Add `astream_generate` method in `backend/core/ports/inference_port.py`:
  ```python
      async def astream_generate(
          self,
          prompt: str,
          system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
          thinking_budget: int = 0,
          thinking_mode: bool = False,
          include_logprobs: bool = False,
          **kwargs,
      ):
          """Génère du texte en flux de manière asynchrone via run_in_executor."""
          import asyncio
          from typing import AsyncGenerator
          queue = asyncio.Queue()
          loop = asyncio.get_running_loop()
          DONE = object()

          def producer():
              try:
                  for chunk in self.stream_generate(
                      prompt=prompt,
                      system_prompt=system_prompt,
                      thinking_budget=thinking_budget,
                      thinking_mode=thinking_mode,
                      include_logprobs=include_logprobs,
                      **kwargs,
                  ):
                      loop.call_soon_threadsafe(queue.put_nowait, chunk)
              except Exception as e:
                  loop.call_soon_threadsafe(queue.put_nowait, e)
              finally:
                  loop.call_soon_threadsafe(queue.put_nowait, DONE)

          loop.run_in_executor(None, producer)

          while True:
              item = await queue.get()
              if item is DONE:
                  break
              if isinstance(item, Exception):
                  raise item
              yield item
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_inference_port_astream_generate_wraps_sync -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add backend/core/ports/inference_port.py tests/adapters/test_async_stream.py
  git commit -m "feat: add async stream wrapper default to InferencePort"
  ```

---

### Task 2: Native Async Streaming in BrainAPIAdapter

**Files:**
- Modify: [brain_api_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/brain_api_adapter.py)
- Test: [test_async_stream.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/adapters/test_async_stream.py)

- [ ] **Step 1: Write the failing test**
  Add a test verifying `BrainAPIAdapter.astream_generate` utilizes `httpx.AsyncClient` to perform native non-blocking async HTTP streaming.
  ```python
  import httpx
  from unittest.mock import MagicMock, AsyncMock, patch
  from adapters.inference.brain_api_adapter import BrainAPIAdapter

  @pytest.mark.asyncio
  async def test_brain_api_adapter_astream_generate_native():
      adapter = BrainAPIAdapter(api_url="http://brain:5000", api_key="dev-key")
      mock_response = AsyncMock()
      mock_response.aiter_text.return_value = ["a", "b", "c"]
      
      # Mock the async stream context manager
      mock_client = MagicMock()
      mock_client.stream.return_value.__aenter__.return_value = mock_response
      
      with patch("adapters.inference.brain_api_adapter.httpx.AsyncClient", return_value=mock_client):
          chunks = []
          async for chunk in adapter.astream_generate("Q"):
              chunks.append(chunk.text)
          
      assert chunks == ["a", "b", "c"]
      mock_client.stream.assert_called_once()
      args, kwargs = mock_client.stream.call_args
      assert args == ("POST", "http://brain:5000/stream_generate")
      assert kwargs["json"]["prompt"] == "Q"
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_brain_api_adapter_astream_generate_native -v`
  Expected: FAIL with `AssertionError`

- [ ] **Step 3: Write minimal implementation**
  Add `astream_generate` to `backend/adapters/inference/brain_api_adapter.py`:
  ```python
      async def astream_generate(
          self,
          prompt: str,
          system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
          thinking_budget: int = 0,
          thinking_mode: bool = False,
          include_logprobs: bool = False,
          **kwargs,
      ):
          """Appelle l'API Brain pour générer du texte en streaming de façon asynchrone."""
          if not self.api_url:
              raise ValueError("Brain API URL not configured")

          payload = {
              "prompt": prompt,
              "system_prompt": system_prompt,
              "thinking_budget": thinking_budget,
              "thinking_mode": thinking_mode,
              "include_logprobs": include_logprobs,
              **kwargs,
          }

          try:
              async with httpx.AsyncClient() as client:
                  async with client.stream(
                      "POST",
                      f"{self.api_url}/stream_generate",
                      json=payload,
                      headers=self._get_headers(),
                      timeout=None,
                  ) as response:
                      response.raise_for_status()
                      async for chunk in response.aiter_text():
                          yield InferenceResponse(text=chunk)
          except httpx.HTTPStatusError as e:
              logger.error(f"BrainAPI Streaming Generation HTTP error: {e}")
              raise
          except httpx.RequestError as e:
              logger.error(f"BrainAPI Streaming Generation network error: {e}")
              raise
          except Exception as e:
              logger.error(f"BrainAPI Streaming Generation failed: {e}")
              raise
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_brain_api_adapter_astream_generate_native -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add backend/adapters/inference/brain_api_adapter.py tests/adapters/test_async_stream.py
  git commit -m "feat: implement native async streaming in BrainAPIAdapter"
  ```

---

### Task 3: Async Fallback Routing in FallbackInferenceAdapter

**Files:**
- Modify: [fallback_adapter.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/adapters/inference/fallback_adapter.py)
- Test: [test_async_stream.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/adapters/test_async_stream.py)

- [ ] **Step 1: Write the failing test**
  Write a test that verifies `FallbackInferenceAdapter.astream_generate` routes correctly to the first working async stream and falls back gracefully.
  ```python
  from adapters.inference.fallback_adapter import FallbackInferenceAdapter

  class CrashAsyncAdapter(InferencePort):
      def generate(self, prompt, **kwargs): raise NotImplementedError
      def get_text_embedding(self, text): return []
      def health_check(self): return {"status": "online"}
      async def astream_generate(self, prompt, **kwargs):
          raise RuntimeError("crash")

  class WorkingAsyncAdapter(InferencePort):
      def generate(self, prompt, **kwargs): raise NotImplementedError
      def get_text_embedding(self, text): return []
      def health_check(self): return {"status": "online"}
      async def astream_generate(self, prompt, **kwargs):
          yield InferenceResponse(text="working")

  @pytest.mark.asyncio
  async def test_fallback_adapter_astream_generate_failover():
      adapter1 = CrashAsyncAdapter()
      adapter2 = WorkingAsyncAdapter()
      fb = FallbackInferenceAdapter([adapter1, adapter2])
      chunks = []
      async for chunk in await fb.astream_generate("Q"):
          chunks.append(chunk.text)
      assert chunks == ["working"]
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_fallback_adapter_astream_generate_failover -v`
  Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
  Add `astream_generate` in `backend/adapters/inference/fallback_adapter.py`:
  ```python
      async def astream_generate(
          self,
          prompt: str,
          system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku.",
          thinking_budget: int = 0,
          thinking_mode: bool = False,
          include_logprobs: bool = False,
          **kwargs,
      ):
          """Streaming asynchrone avec repli intelligent."""
          capable_adapters = self._capability_cache.get("astream_generate", [])
          if not capable_adapters:
              capable_adapters = self._capability_cache.get("stream_generate", [])
          if not capable_adapters:
              capable_adapters = self.adapters

          ordered_adapters = self._get_ordered_adapters(capable_adapters)
          for adapter in ordered_adapters:
              if not hasattr(adapter, "astream_generate") or not callable(
                  getattr(adapter, "astream_generate")
              ):
                  continue
              start_time = time.time()
              try:
                  import inspect
                  sig = inspect.signature(adapter.astream_generate)
                  call_kwargs: Dict[str, Any] = {
                      "thinking_budget": thinking_budget,
                      "thinking_mode": thinking_mode,
                  }
                  if "include_logprobs" in sig.parameters:
                      call_kwargs["include_logprobs"] = include_logprobs
                  call_kwargs.update(kwargs)

                  gen = adapter.astream_generate(prompt, system_prompt, **call_kwargs)
                  try:
                      first_chunk = await gen.__anext__()
                  except StopAsyncIteration:
                      self._report_failure(
                          adapter,
                          "astream_generate",
                          "StopAsyncIteration (Pas de réponse)",
                          time.time() - start_time,
                          prompt,
                      )
                      continue

                  latency = time.time() - start_time

                  if first_chunk and not first_chunk.is_error:
                      async def success_gen():
                          yield first_chunk
                          async for chunk in gen:
                              yield chunk

                      logger.info(
                          f"✅ [Async Stream Fallback] {adapter.__class__.__name__} success in {latency:.2f}s"
                      )
                      return success_gen()

                  error_hint = first_chunk.text if first_chunk else "Premier chunk vide"
                  self._report_failure(
                      adapter, "astream_generate", error_hint, latency, prompt
                  )
              except Exception as e:
                  self._report_failure(
                      adapter,
                      "astream_generate",
                      f"CRASH: {str(e)}",
                      time.time() - start_time,
                      prompt,
                  )
                  continue

          async def error_gen():
              import asyncio
              loop = asyncio.get_running_loop()
              res = await loop.run_in_executor(
                  None,
                  lambda: self.generate(
                      prompt, system_prompt, thinking_budget, thinking_mode, include_logprobs, **kwargs
                  )
              )
              yield res

          return error_gen()
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_fallback_adapter_astream_generate_failover -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add backend/adapters/inference/fallback_adapter.py tests/adapters/test_async_stream.py
  git commit -m "feat: add astream_generate fallback routing to FallbackInferenceAdapter"
  ```

---

### Task 4: Expose astream_generate in LLMService

**Files:**
- Modify: [llm_service.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/llm_service.py)
- Test: [test_async_stream.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/adapters/test_async_stream.py)

- [ ] **Step 1: Write the failing test**
  Add a test verifying that `LLMService.astream_generate` correctly forwards call kwargs to the underlying engine's `astream_generate`.
  ```python
  from core.domain.services.llm_service import LLMService

  @pytest.mark.asyncio
  async def test_llm_service_astream_generate_delegation():
      mock_engine = MagicMock()
      
      async def fake_astream(prompt, **kwargs):
          yield InferenceResponse(text="tokens")
          
      mock_engine.astream_generate.side_effect = fake_astream
      
      service = LLMService(inference_engine=mock_engine, prompt_manager=MagicMock())
      chunks = []
      async for chunk in service.astream_generate("Q"):
          chunks.append(chunk.text)
          
      assert chunks == ["tokens"]
      mock_engine.astream_generate.assert_called_once_with(
          "Q", "", thinking_budget=0, thinking_mode=False
      )
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_llm_service_astream_generate_delegation -v`
  Expected: FAIL with `AttributeError: 'LLMService' object has no attribute 'astream_generate'`

- [ ] **Step 3: Write minimal implementation**
  Add `astream_generate` in `backend/core/domain/services/llm_service.py`:
  ```python
      async def astream_generate(
          self,
          prompt: str,
          system_prompt: str = "",
          use_slm: bool = False,
          thinking_budget: int = 0,
          thinking_mode: bool = False,
          **kwargs,
      ) -> AsyncGenerator[InferenceResponse, None]:
          """Version streaming asynchrone de la génération, supportant le routage SLM."""
          engine = self.slm_engine if use_slm else self.inference_engine
          async for chunk in engine.astream_generate(
              prompt,
              system_prompt,
              thinking_budget=thinking_budget,
              thinking_mode=thinking_mode,
              **kwargs,
          ):
              yield chunk
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py::test_llm_service_astream_generate_delegation -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add backend/core/domain/services/llm_service.py tests/adapters/test_async_stream.py
  git commit -m "feat: expose astream_generate in LLMService"
  ```

---

### Task 5: Stream Concurrency Verification

**Files:**
- Test: [test_async_stream.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/adapters/test_async_stream.py)

- [ ] **Step 1: Write and run concurrency test**
  Add a test to `tests/adapters/test_async_stream.py` that streams two requests in parallel using `asyncio.gather` and asserts that they can execute concurrently without blocking each other.
  ```python
  @pytest.mark.asyncio
  async def test_concurrent_streaming():
      class SlowAsyncAdapter(InferencePort):
          def generate(self, prompt, **kwargs): raise NotImplementedError
          def get_text_embedding(self, text): return []
          def health_check(self): return {"status": "online"}
          async def astream_generate(self, prompt, **kwargs):
              yield InferenceResponse(text=f"{prompt}-1")
              await asyncio.sleep(0.1)
              yield InferenceResponse(text=f"{prompt}-2")

      adapter = SlowAsyncAdapter()

      async def consume(prompt):
          res = []
          async for chunk in adapter.astream_generate(prompt):
              res.append(chunk.text)
          return res

      # Consume concurrently
      start = asyncio.get_running_loop().time()
      results = await asyncio.gather(consume("A"), consume("B"))
      duration = asyncio.get_running_loop().time() - start

      assert results == [["A-1", "A-2"], ["B-1", "B-2"]]
      # Because of parallel asyncio.sleep, total duration should be ~0.1s instead of 0.2s
      assert duration < 0.18
  ```

- [ ] **Step 2: Run test to verify it passes**
  Run: `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py -v`
  Expected: PASS

- [ ] **Step 3: Commit**
  ```bash
  git add tests/adapters/test_async_stream.py
  git commit -m "test: verify concurrent streaming works using asyncio.gather"
  ```

---

## Verification Plan

### Automated Tests
- Run all async stream adapter tests:
  `..\..\.venv\Scripts\pytest tests/adapters/test_async_stream.py -v`
- Run fallback adapter regression tests:
  `..\..\.venv\Scripts\pytest tests/adapters/test_fallback_adapter.py -v`
