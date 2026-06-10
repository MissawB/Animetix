# Gemini Enterprise Agent Platform (Agent Gateway & Observability) Design Spec

This design document outlines the integration of Gemini Enterprise Agent Platform components—specifically Agent Gateway for prompt security policy enforcement and Agent Observability for reasoning path visualization—into Animetix. It maintains full backward compatibility with local regex and LLM-moderation prompt fallbacks.

## User Review Required

> [!IMPORTANT]
> The Agent Gateway acts as the first line of defense in `GuardrailService`, pre-evaluating user inputs and AI outputs against a central Vertex AI Policy. If the API fails or is inactive, the system falls back gracefully to local regex patterns and local LLM moderation prompts.

> [!NOTE]
> Agent Observability is implemented by enriching OpenTelemetry spans with GCP-specific semantic attributes (`gcp.agent.*`). This ensures visual visualization in the GCP Cloud Trace and Agent Observability consoles without requiring specialized tracer SDKs.

## Proposed Changes

---

### Backend Config & Environment

#### [MODIFY] [settings.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/api/animetix_project/settings.py)
*   Define settings for Agent Gateway and Agent Observability:
    ```python
    VERTEX_AI_AGENT_GATEWAY_ACTIVE = env.bool('VERTEX_AI_AGENT_GATEWAY_ACTIVE', default=False)
    VERTEX_AI_AGENT_POLICY_ID = env('VERTEX_AI_AGENT_POLICY_ID', default='')
    VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE = env.bool('VERTEX_AI_AGENT_OBSERVABILITY_ACTIVE', default=False)
    VERTEX_AI_AGENT_ID = env('VERTEX_AI_AGENT_ID', default='animetix-core-rag-agent')
    ```

---

### Guardrails & Security

#### [MODIFY] [guardrail_service.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/guardrail_service.py)
*   Implement `_check_agent_gateway(self, text, mode)` to evaluate policies against Vertex AI.
*   Update `validate_input()` and `validate_output()` to query `_check_agent_gateway()` at the very beginning of the validation flow.

---

### Agentic RAG Observability

#### [MODIFY] [agentic_rag_service.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/backend/core/domain/services/agentic_rag_service.py)
*   Implement `_record_agent_trace(self, state_name, details)` to set attributes on the current OpenTelemetry span.
*   Enrich state transition steps (`PLAN`, `SEARCH`, `SYNTHESIZE`, etc.) by calling `_record_agent_trace()`.

---

### Automated Tests

#### [NEW] [test_agent_observability_gateway.py](file:///c:/Users/bahma/PycharmProjects/Projet%20solo/Double_scenario_Project/tests/core/test_agent_observability_gateway.py)
*   Create a test suite to verify:
    *   `GuardrailService` invokes Vertex AI Agent Gateway when enabled and handles violations.
    *   Graceful fallback to local guardrails when Agent Gateway is disabled or raises an exception.
    *   `AgenticRAGService` records OpenTelemetry trace attributes during states execution when Agent Observability is active.

## Verification Plan

### Automated Tests
Run the pytest suite:
```bash
.venv\Scripts\pytest tests/core/test_agent_observability_gateway.py -v
```
