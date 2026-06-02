# Design Spec: Advanced Explainability (XAI) - Semantic Middleware

**Date:** 2026-06-02
**Status:** Draft
**Topic:** Advanced XAI implementation for Animetix (Hybrid approach).

## 1. Goal
Provide a "Full Stack" explainability layer that answers both "What is the model thinking?" (internal diagnostics) and "Why did it give this answer?" (RAG attribution).

## 2. Architecture
The system follows a **Semantic Middleware** pattern where diagnostics are captured in real-time during the RAG workflow and aggregated into a structured report.

### Components:
- **`XaiCollector`**: A transient object used during a single RAG request to collect step-by-step metadata (Search results, agent thoughts, internal activations).
- **`XaiDiagnosticService` (Upgraded)**: Orchestrates the aggregation of collector data and raw model diagnostics (Attention, Logits).
- **`XaiReport`**: The final structured entity returned to the consumer.

## 3. Data Structures (Domain Entities)

```python
class DocumentAttribution(BaseModel):
    document_id: str
    title: str
    relevance_score: float
    contribution_weight: float # Calculated based on attention

class ModelDiagnostics(BaseModel):
    attention_heatmap: List[List[float]]
    top_influential_tokens: List[str]
    logit_lens_trajectory: List[Dict[str, Any]]

class XaiReport(BaseModel):
    request_id: str
    query_intent: str
    retrieval_attribution: List[DocumentAttribution]
    internal_diagnostics: Optional[ModelDiagnostics]
    uncertainty: Dict[str, Any]
    agent_trace: List[Dict[str, Any]]
    final_confidence: float
```

## 4. Implementation Strategy

### 4.1. Real-time Capture
- Modify `RAGWorkflowManager` to accept an optional `XaiCollector`.
- Add hooks in `_handle_plan`, `_handle_research`, and `_handle_synthesize` to log events.

### 4.2. Diagnostic Enrichment
- Update `XaiDiagnosticService.explain_response` to:
    1. Fetch raw diagnostics from `InferencePort`.
    2. Correlate attention weights with the retrieved documents in the `XaiCollector`.
    3. Calculate a "Source Influence" score.

### 4.3. InferencePort Alignment
- Ensure `UnifiedInferenceAdapter` returns attention maps and logit lens data in a consistent format (fixing existing key mismatches).

## 5. Error Handling
- XAI failure should **never** block the main inference.
- If diagnostics fail, return an empty `XaiReport` with an error flag.

## 6. Testing Strategy
- **Unit Tests:** Verify `XaiCollector` correctly stores data.
- **Integration Tests:** Run a full RAG workflow and check the presence of `XaiReport` in the response.
- **Accuracy Tests:** Manually verify that high-attention tokens correspond to the information extracted from the top documents.
