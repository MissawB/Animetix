# Dynamic Capability Introspection & Intelligent Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement dynamic method override introspection in `FallbackInferenceAdapter` to optimize execution latency and avoid false-positive observability error logging.

**Architecture:** Detect overridden methods at startup by sifting raw bound functions against `InferencePort` methods. Filter `InferenceNotImplementedError` quietly to keep MLOps dashboards pollution-free.

**Tech Stack:** Python 3.11, Pytest, dependency-injector, Django.

---

### Task 1: Add and Test Dynamic Introspection Engine

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`
- Modify: `tests/adapters/test_fallback_structured.py`

- [ ] **Step 1: Write the failing test for capability introspection**
Add these test cases to `tests/adapters/test_fallback_structured.py`:
```python
from core.ports.inference_port import InferencePort

class MockCapableAdapter(InferencePort):
    def estimate_depth(self, image_data: bytes) -> bytes:
        return b"depth_map"
        
    def health_check(self) -> dict:
        return {"status": "online"}

class MockGenericAdapter(InferencePort):
    def health_check(self) -> dict:
        return {"status": "online"}

def test_fallback_introspection_capability_mapping():
    adapter1 = MockGenericAdapter()
    adapter2 = MockCapableAdapter()
    fallback = FallbackInferenceAdapter(adapters=[adapter1, adapter2])
    
    # Introspection checks
    assert fallback._is_method_overridden(adapter2, "estimate_depth") is True
    assert fallback._is_method_overridden(adapter1, "estimate_depth") is False
    
    # Capability cache verification
    capable = fallback._capability_cache.get("estimate_depth", [])
    assert adapter2 in capable
    assert adapter1 not in capable
```

- [ ] **Step 2: Run test to verify it fails**
Run:
```powershell
pytest tests/adapters/test_fallback_structured.py::test_fallback_introspection_capability_mapping -v
```
Expected: FAIL due to AttributeError (methods `_is_method_overridden` and `_capability_cache` not existing).

- [ ] **Step 3: Implement minimal introspection code**
Add to `backend/adapters/inference/fallback_adapter.py` inside `FallbackInferenceAdapter`:
```python
    def __init__(self, adapters: List[InferencePort], obs_service: Optional[Any] = None):
        self.adapters = [a for a in adapters if a is not None]
        self.obs_service = obs_service
        self._capability_cache = {}
        self._build_capability_cache()

    def _is_method_overridden(self, adapter: InferencePort, method_name: str) -> bool:
        method = getattr(adapter, method_name, None)
        if method is None or not callable(method):
            return False
            
        port_method = getattr(InferencePort, method_name, None)
        if port_method is None:
            return True
            
        adapter_func = getattr(method, "__func__", method)
        port_func = getattr(port_method, "__func__", port_method)
        
        return adapter_func is not port_func

    def _build_capability_cache(self) -> None:
        import inspect
        from core.ports.inference_port import InferencePort
        
        port_methods = [
            name for name, val in inspect.getmembers(InferencePort, predicate=inspect.isfunction)
            if not name.startswith("_")
        ]
        
        for method_name in port_methods:
            capable = [
                adapter for adapter in self.adapters
                if self._is_method_overridden(adapter, method_name)
            ]
            self._capability_cache[method_name] = capable
            logger.debug(f"⚙️ [Fallback] Registered capable engines for '{method_name}': {[a.__class__.__name__ for a in capable]}")
```

- [ ] **Step 4: Run test to verify it passes**
Run:
```powershell
pytest tests/adapters/test_fallback_structured.py::test_fallback_introspection_capability_mapping -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/adapters/inference/fallback_adapter.py tests/adapters/test_fallback_structured.py
git commit -m "feat: implement dynamic method override capability introspection in fallback adapter"
```

---

### Task 2: Test and Implement Direct Routing of Specialized Calls

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`
- Modify: `tests/adapters/test_fallback_structured.py`

- [ ] **Step 1: Write failing test for direct capability routing**
Add this test to `tests/adapters/test_fallback_structured.py`:
```python
def test_fallback_call_routes_directly_to_capable_adapters():
    adapter1 = MockGenericAdapter()
    # Mocking standard Port methods that generic adapter should not execute
    adapter1.estimate_depth = MagicMock(side_effect=Exception("Should not be called"))
    
    adapter2 = MockCapableAdapter()
    adapter2.estimate_depth = MagicMock(return_value=b"correct_depth")
    
    fallback = FallbackInferenceAdapter(adapters=[adapter1, adapter2])
    
    result = fallback.estimate_depth(b"sample_image")
    
    assert result == b"correct_depth"
    adapter1.estimate_depth.assert_not_called()
    adapter2.estimate_depth.assert_called_once_with(b"sample_image")
```

- [ ] **Step 2: Run test to verify it fails**
Run:
```powershell
pytest tests/adapters/test_fallback_structured.py::test_fallback_call_routes_directly_to_capable_adapters -v
```
Expected: FAIL (adapter1 gets called and raises the exception, since fallback loop currently calls every adapter sequentially).

- [ ] **Step 3: Modify `_fallback_call` to route dynamically using `_capability_cache`**
Update `_fallback_call` in `backend/adapters/inference/fallback_adapter.py`:
```python
    def _fallback_call(self, method_name: str, *args, **kwargs):
        capable_adapters = self._capability_cache.get(method_name, [])
        if not capable_adapters:
            capable_adapters = self.adapters

        for adapter in capable_adapters:
            if not hasattr(adapter, method_name) or not callable(getattr(adapter, method_name)):
                continue
            start_time = time.time()
            try:
                method = getattr(adapter, method_name)
                res = method(*args, **kwargs)
                latency = time.time() - start_time
                
                if res is not None: 
                    logger.info(f"✅ [Fallback] {adapter.__class__.__name__}.{method_name} success in {latency:.2f}s")
                    return res
                
                self._report_failure(adapter, method_name, "Résultat None", latency)
            except Exception as e:
                latency = time.time() - start_time
                self._report_failure(adapter, method_name, f"CRASH: {str(e)}", latency)
                continue
        return None
```

- [ ] **Step 4: Run test to verify it passes**
Run:
```powershell
pytest tests/adapters/test_fallback_structured.py::test_fallback_call_routes_directly_to_capable_adapters -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/adapters/inference/fallback_adapter.py tests/adapters/test_fallback_structured.py
git commit -m "feat: optimize fallback adapter to route directly to capable adapters via dynamic cache"
```

---

### Task 3: Test and Implement Quiet NotImplementedError Handling

**Files:**
- Modify: `backend/adapters/inference/fallback_adapter.py`
- Modify: `tests/adapters/test_fallback_structured.py`

- [ ] **Step 1: Write failing test for quiet NotImplementedError handling**
Add this test to `tests/adapters/test_fallback_structured.py`:
```python
from core.ports.inference_port import InferenceNotImplementedError

def test_not_implemented_exception_is_silent_and_does_not_log_error():
    mock_obs = MagicMock()
    
    adapter1 = MockCapableAdapter()
    adapter1.estimate_depth = MagicMock(side_effect=InferenceNotImplementedError("Dynamic override disabled"))
    
    adapter2 = MockCapableAdapter()
    adapter2.estimate_depth = MagicMock(return_value=b"correct_depth_2")
    
    fallback = FallbackInferenceAdapter(adapters=[adapter1, adapter2], obs_service=mock_obs)
    
    with patch("src.adapters.inference.fallback_adapter.logger.error") as mock_log_err:
        result = fallback.estimate_depth(b"sample_image")
        
        assert result == b"correct_depth_2"
        # Verify NO error log was written and NO observability error was recorded for the NotImplemented event
        mock_log_err.assert_not_called()
        mock_obs.log_error.assert_not_called()
```
*Note: Make sure to import `patch` from `unittest.mock` inside the test.*

- [ ] **Step 2: Run test to verify it fails**
Run:
```powershell
pytest tests/adapters/test_fallback_structured.py::test_not_implemented_exception_is_silent_and_does_not_log_error -v
```
Expected: FAIL (errors are logged and reported since `Exception` catch-all intercepts `InferenceNotImplementedError` and reports it).

- [ ] **Step 3: Modify exception handling in `_fallback_call`**
Modify the try-except block in `_fallback_call` inside `backend/adapters/inference/fallback_adapter.py`:
```python
            except (InferenceNotImplementedError, NotImplementedError):
                # Ignorer silencieusement la non-implémentation
                continue
            except Exception as e:
                latency = time.time() - start_time
                self._report_failure(adapter, method_name, f"CRASH: {str(e)}", latency)
                continue
```
*Also ensure `from core.ports.inference_port import InferenceNotImplementedError` is properly imported in `fallback_adapter.py`.*

- [ ] **Step 4: Run all fallback structured tests to verify they all pass**
Run:
```powershell
pytest tests/adapters/test_fallback_structured.py -v
```
Expected: PASS (all tests, including existing structured tests, pass perfectly).

- [ ] **Step 5: Commit**
```bash
git add backend/adapters/inference/fallback_adapter.py tests/adapters/test_fallback_structured.py
git commit -m "feat: ignore InferenceNotImplementedError silently without error logs or metric pollution"
```

---

### Task 4: Run Full Test Suite & Validation

**Files:**
- None (Validation phase)

- [ ] **Step 1: Run the full adapter test suite**
Run:
```powershell
pytest tests/adapters/ -v
```
Expected: PASS on all adapters.

- [ ] **Step 2: Run the full core test suite**
Run:
```powershell
pytest tests/core/ -v
```
Expected: PASS on all core tests.
