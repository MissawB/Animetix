# Admin Tools Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize and connect the Admin monitoring tools (DPO Curation, SOTA Benchmarks, Graph Healer) to their backend services.

**Architecture:** Standardize API endpoints as `APIView` components and complete the domain logic for DPO curation.

**Tech Stack:** Django REST Framework, Python 3.11+, Neo4j, Pydantic.

---

### Task 1: Complete DPO Domain Logic

**Files:**
- Modify: `backend/core/domain/services/dpo_feedback_loop.py`
- Test: `tests/core/test_dpo_logic.py`

- [ ] **Step 1: Write the failing test for curation**

```python
import pytest
from unittest.mock import MagicMock
from core.domain.services.dpo_feedback_loop import DPOFeedbackLoop

def test_curate_feedback_success():
    feedback_port = MagicMock()
    # Mock finding feedback
    feedback_port.get_recent_feedback.return_value = [{"id": 123, "input_context": "q", "output_text": "bad"}]
    
    loop = DPOFeedbackLoop(feedback_port=feedback_port)
    
    # This method doesn't exist yet
    result = loop.curate_feedback(feedback_id=123, chosen_text="perfect response")
    
    assert result is True
    # Verify it attempted to save/create something (we'll implement the logic)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_dpo_logic.py`
Expected: FAIL (AttributeError: 'DPOFeedbackLoop' object has no attribute 'curate_feedback')

- [ ] **Step 3: Implement curate_feedback method**

```python
    def curate_feedback(self, feedback_id: int, chosen_text: str) -> bool:
        """
        Manually validates a rejected feedback by providing the 'Chosen' alternative.
        Persists as a GoldDatasetEntry.
        """
        from animetix.models import AIFeedback, GoldDatasetEntry
        try:
            fb = AIFeedback.objects.get(id=feedback_id)
            # Create or update gold entry
            GoldDatasetEntry.objects.update_or_create(
                source_feedback=fb,
                defaults={
                    "context": fb.input_context,
                    "instruction": "Generate high quality response",
                    "response": chosen_text,
                    "is_validated": True
                }
            )
            logger.info(f"✅ Feedback {feedback_id} curated into Gold Dataset.")
            return True
        except Exception as e:
            logger.error(f"❌ Curation failed for feedback {feedback_id}: {e}")
            return False
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add backend/core/domain/services/dpo_feedback_loop.py
git commit -m "feat(mlops): implement curate_feedback logic in DPOFeedbackLoop"
```

---

### Task 2: Standardize and Activate Admin API Views

**Files:**
- Modify: `backend/api/animetix/api/mlops.py`
- Modify: `backend/api/animetix/urls/api.py`

- [ ] **Step 1: Refactor DPOCurationViewSet to DPOCurationView**

In `mlops.py`, replace `DPOCurationViewSet` with:
```python
class DPOCurationView(APIView):
    """API for DPO Curation (List and Post)."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        container = get_container()
        dpo_loop = container.core.dpo_feedback_loop()
        limit = int(request.GET.get('limit', 50))
        samples = dpo_loop.get_rejected_for_curation(limit=limit)
        return Response(samples)

    def post(self, request):
        container = get_container()
        dpo_loop = container.core.dpo_feedback_loop()
        feedback_id = request.data.get('feedback_id')
        chosen_text = request.data.get('chosen_text')
        
        if not feedback_id or not chosen_text:
            return Response({'error': 'feedback_id and chosen_text are required'}, status=400)
            
        success = dpo_loop.curate_feedback(feedback_id, chosen_text)
        if success:
            return Response({'status': 'success', 'message': 'Feedback successfully curated.'})
        return Response({'error': 'Curation failed'}, status=500)
```

- [ ] **Step 2: Update URL routing**

Uncomment and update paths in `backend/api/animetix/urls/api.py`:
```python
    path('mlops/dpo/curation/', api_views.DPOCurationView.as_view(), name='api_dpo_curation'),
    path('mlops/sota/benchmarks/', api_views.SOTABenchmarkListView.as_view(), name='api_sota_benchmarks'),
    path('graph/debugger/', api_views.GraphDebuggerView.as_view(), name='api_graph_debugger'),
```

- [ ] **Step 3: Export in proxy file**

Ensure `backend/api/animetix/api_views.py` includes `DPOCurationView`.

- [ ] **Step 4: Commit**

```bash
git add backend/api/animetix/api/mlops.py backend/api/animetix/urls/api.py backend/api/animetix/api_views.py
git commit -m "feat(admin): activate and standardize DPO, SOTA, and Graph Debugger endpoints"
```

---

### Task 3: Final Validation

- [ ] **Step 1: Run integration test for DPO endpoint**
- [ ] **Step 2: Verify SOTA metadata is returned**
- [ ] **Step 3: Verify Graph Debugger audit is functional**
