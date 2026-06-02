# Design Doc: LLMService Refactoring - Token Tracking and Guardrails Optimization

**Author:** Gemini CLI
**Date:** 2024-05-22
**Status:** Draft

## 1. Overview
This document outlines the refactoring of `backend/core/domain/services/llm_service.py` to consolidate redundant token tracking logic and optimize the implementation of forbidden terms (guardrails).

## 2. Proposed Changes

### 2.1 Centralized Token Calculation
Currently, token tracking logic is duplicated for Weight & Biases (W&B) observability and for the local usage port. Each block re-implements the logic for checking `response_obj.metadata.usage` and falling back to a heuristic (`len // 4`).

**Design:**
Introduce a private helper method:
```python
def _get_token_usage(self, response_obj: InferenceResponse, prompt: str, system_prompt: str) -> Tuple[int, int, int]:
    """
    Calculates input, output, and total tokens.
    Returns: (input_tokens, output_tokens, total_tokens)
    """
```
This method will:
1. Prioritize `response_obj.metadata.usage` (keys: `prompt_tokens`, `completion_tokens`, `total_tokens`).
2. Fall back to the `// 4` heuristic based on `prompt`, `system_prompt`, and `response_obj.text`.

### 2.2 Optimized Forbidden Terms
Currently, the service iterates over `forbidden_terms` and performs a `re.sub` for each term. This is inefficient if the list is long or if terms overlap.

**Design:**
Combine all forbidden terms into a single regular expression pattern:
```python
if forbidden_terms:
    valid_terms = [re.escape(t) for t in forbidden_terms if t]
    if valid_terms:
        pattern = re.compile("|".join(valid_terms), re.IGNORECASE)
        res = pattern.sub("[CENSURÉ]", res)
```
This performs a single pass over the result string.

## 3. Implementation Details

### LLMService.generate refactor:
1. Call `_get_token_usage` once.
2. Use the results in both logging blocks.
3. Replace the loop for `forbidden_terms` with a single regex substitution.

## 4. Testing Strategy
- **Unit Tests:** Update `tests/core/test_llm_service.py` to:
    - Mock `InferenceResponse` with and without metadata usage.
    - Verify that `log_usage` and `log_inference` receive the correct token counts.
    - Verify that multiple forbidden terms are correctly censored in one pass.
