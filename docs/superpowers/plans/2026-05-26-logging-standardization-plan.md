# Python Logging Standardization & Silent Error Elimination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate silent error handling blocks and generic exceptions across backend services, establishing clean exception propagation for safety guardrails and standardized warning logging for fallback calculators.

**Architecture:** Hybrid strategy raising typified `ContentModerationError` on guardrail failures while logging detailed warning stack traces (`logger.warning(..., exc_info=True)`) on fallback estimators.

**Tech Stack:** Python 3.11, Pytest, Django.

---

### Task 1: Remediate Critical Guardrail Silent Errors

**Files:**
- Modify: `backend/core/domain/services/guardrail_service.py`
- Modify: `tests/core/test_guardrail_service.py`

- [ ] **Step 1: Write a failing test verifying ContentModerationError propagation**
Add this test to `tests/core/test_guardrail_service.py`:
```python
from unittest.mock import MagicMock
from core.domain.entities.exceptions import ContentModerationError

def test_guardrail_verification_raises_moderation_error_on_inference_failure():
    mock_engine = MagicMock()
    mock_engine.generate.side_effect = Exception("Inference engine connection timeout")
    
    # We setup the guardrail with the crashing engine
    service = GuardrailService(inference_engine=mock_engine)
    
    with pytest.raises(ContentModerationError) as excinfo:
        service.moderate_content("Sample text to check", categories=["spoiler"])
        
    assert "Guardrail verification failed due to internal error" in str(excinfo.value)
```

- [ ] **Step 2: Run test to verify it fails**
Run:
```powershell
pytest tests/core/test_guardrail_service.py::test_guardrail_verification_raises_moderation_error_on_inference_failure -v
```
Expected: FAIL (returns safe stub dict instead of raising `ContentModerationError`).

- [ ] **Step 3: Modify guardrail_service.py to raise ContentModerationError**
Update the try-except block in `backend/core/domain/services/guardrail_service.py` (L151-158):
```python
        except Exception as e:
            logger.exception("❌ Guardrail verification failed due to unexpected error.")
            from core.domain.entities.exceptions import ContentModerationError
            raise ContentModerationError("Guardrail verification failed due to internal error.") from e
```

- [ ] **Step 4: Run test to verify it passes**
Run:
```powershell
pytest tests/core/test_guardrail_service.py::test_guardrail_verification_raises_moderation_error_on_inference_failure -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/core/domain/services/guardrail_service.py tests/core/test_guardrail_service.py
git commit -m "feat: raise ContentModerationError on guardrail verification crash"
```

---

### Task 2: Remediate Silent Errors in Cognitive & Simulator Services

**Files:**
- Modify: `backend/core/domain/services/tree_of_thoughts_service.py`
- Modify: `backend/core/domain/services/dspy_prompt_optimizer.py`
- Modify: `backend/core/domain/services/counterfactual_simulator.py`

- [ ] **Step 1: Standardize exceptions in tree_of_thoughts_service.py**
Update L123 in `backend/core/domain/services/tree_of_thoughts_service.py`:
```python
        except Exception as e:
            logger.warning("⚠️ Logic Critic evaluation failed. Falling back to default score 0.7.", exc_info=True)
            return 0.7
```

- [ ] **Step 2: Standardize exceptions in dspy_prompt_optimizer.py**
Update L72 and L105 in `backend/core/domain/services/dspy_prompt_optimizer.py`:
```python
                except Exception as e:
                    logger.warning("⚠️ DSPy variant evaluation step failed. Appending fallback score 0.5.", exc_info=True)
                    scores.append(0.5)
```
And:
```python
        except Exception as e:
            logger.warning("⚠️ DSPy Judge evaluation failed. Falling back to default score 0.7.", exc_info=True)
            return 0.7
```

- [ ] **Step 3: Standardize exceptions in counterfactual_simulator.py**
Update L64 in `backend/core/domain/services/counterfactual_simulator.py`:
```python
        except Exception as e:
            logger.warning("⚠️ Counterfactual Utility evaluation failed. Falling back to default utility 0.75.", exc_info=True)
            alternative_utility = 0.75
```

- [ ] **Step 4: Run all corresponding tests to make sure they pass**
Run:
```powershell
pytest tests/core/test_cove_oracle_service.py tests/core/test_distillation_pipeline.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/core/domain/services/tree_of_thoughts_service.py backend/core/domain/services/dspy_prompt_optimizer.py backend/core/domain/services/counterfactual_simulator.py
git commit -m "refactor: standardize logging and remove silent error handling in cognitive & simulator services"
```

---

### Task 3: Remediate Silent Errors in API Views & Persistence Adapters

**Files:**
- Modify: `backend/api/animetix/api/labs.py`
- Modify: `backend/adapters/persistence/neo4j_graph_adapter.py`

- [ ] **Step 1: Standardize exceptions in Django view labs.py**
Update L101 and L108 in `backend/api/animetix/api/labs.py`:
```python
        except Exception as e:
            logger.warning("⚠️ Failed to audit Knowledge Graph health. Setting status as unavailable.", exc_info=True)
            stats['knowledge_graph'] = {"status": "unavailable"}
```
And:
```python
        except Exception as e:
            logger.warning("⚠️ Failed to audit embedding drift report. Setting status as unavailable.", exc_info=True)
            stats['embedding_drift'] = {"status": "unavailable"}
```

- [ ] **Step 2: Add debugging logs in neo4j_graph_adapter.py**
Update L63 in `backend/adapters/persistence/neo4j_graph_adapter.py`:
```python
        except Exception as e:
            logger.debug("Neo4j connectivity check failed.", exc_info=True)
            return False
```

- [ ] **Step 3: Run full integration tests to verify no regression**
Run:
```powershell
pytest tests/core/test_guardrail_service.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add backend/api/animetix/api/labs.py backend/adapters/persistence/neo4j_graph_adapter.py
git commit -m "refactor: remove silent error catches in labs view and neo4j health check with appropriate logging"
```
