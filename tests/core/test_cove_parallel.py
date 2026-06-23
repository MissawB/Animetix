"""Tests for the parallelised Chain-of-Verification path.

Étape 3 of CoVe (per-claim verification) used to run linearly: 2 LLM calls
per claim, sequentially. These tests pin the new behaviour:

* ``InferencePort.agenerate`` exposes an async seam over the blocking
  ``generate`` (default delegates to a worker thread).
* ``CoveOracleService.atrace_verification`` fans the per-claim work out with
  ``asyncio.gather`` so claims are verified concurrently.
"""

import asyncio

import pytest
from core.domain.entities.ai_schemas import InferenceResponse
from core.domain.services.cove_oracle_service import CoveOracleService
from core.ports.inference_port import InferencePort


# --- Port: agenerate delegates to the blocking generate ----------------------
@pytest.mark.asyncio
async def test_agenerate_delegates_to_sync_generate_off_thread():
    calls = {}

    class _Adapter(InferencePort):
        def generate(self, prompt, system_prompt="sys", **kwargs):
            calls["prompt"] = prompt
            calls["system_prompt"] = system_prompt
            return InferenceResponse(text=f"echo:{prompt}")

        def stream_generate(self, *a, **k):  # pragma: no cover - unused
            raise NotImplementedError

        def get_text_embedding(self, text):  # pragma: no cover - unused
            raise NotImplementedError

        def health_check(self):  # pragma: no cover - unused
            return {"status": "online"}

    adapter = _Adapter()
    res = await adapter.agenerate("hello", system_prompt="you-are-x")

    assert res.text == "echo:hello"
    assert calls == {"prompt": "hello", "system_prompt": "you-are-x"}


# --- Service: claims are verified concurrently -------------------------------
def _prompt_router(name, **kwargs):
    """Mirror PromptManager: cove_plan / cove_final return (prompt, system)."""
    if name in ("cove_plan", "cove_final"):
        return (name, "system")
    return name


class _ConcurrencyEngine:
    """Async fake that records the peak number of overlapping agenerate calls.

    If Étape 3 is parallelised, every claim issues its first ``agenerate``
    (cove_entities) before any of them finishes, so ``max_concurrent`` reaches
    the number of claims. If it is linear, it never exceeds 1.
    """

    def __init__(self, n_claims):
        self._questions = [f"claim {i}?" for i in range(n_claims)]
        self.active = 0
        self.max_concurrent = 0

    async def agenerate(self, prompt, system_prompt="sys", **kwargs):
        if prompt == "cove_entities":
            self.active += 1
            self.max_concurrent = max(self.max_concurrent, self.active)
            try:
                await asyncio.sleep(0.05)  # hold the slot so overlap is observable
            finally:
                self.active -= 1
            return InferenceResponse(text="EntityA")
        if prompt == "cove_plan":
            payload = '{"verification_questions": %s}' % (
                str(self._questions).replace("'", '"')
            )
            return InferenceResponse(text=payload)
        if prompt == "cove_eval":
            return InferenceResponse(text="verified")
        if prompt == "cove_baseline":
            return InferenceResponse(text="baseline")
        if prompt == "cove_final":
            return InferenceResponse(text="final answer")
        return InferenceResponse(text="")


@pytest.fixture
def prompt_manager():
    from unittest.mock import MagicMock

    pm = MagicMock()
    pm.get_prompt.side_effect = _prompt_router
    return pm


@pytest.mark.asyncio
async def test_atrace_verification_runs_claims_concurrently(prompt_manager):
    engine = _ConcurrencyEngine(n_claims=3)
    svc = CoveOracleService(
        inference_engine=engine,
        prompt_manager=prompt_manager,
        neo4j_manager=None,
    )

    trace = await svc.atrace_verification("Question?", "Anime")

    assert engine.max_concurrent == 3, "claims were not verified concurrently"
    assert len(trace["verifications"]) == 3
    assert trace["final_response"] == "final answer"


@pytest.mark.asyncio
async def test_atrace_verification_no_claims_returns_baseline(prompt_manager):
    class _NoClaimEngine(_ConcurrencyEngine):
        async def agenerate(self, prompt, system_prompt="sys", **kwargs):
            if prompt == "cove_plan":
                return InferenceResponse(text="{}")
            return await super().agenerate(prompt, system_prompt, **kwargs)

    engine = _NoClaimEngine(n_claims=0)
    svc = CoveOracleService(
        inference_engine=engine,
        prompt_manager=prompt_manager,
        neo4j_manager=None,
    )

    trace = await svc.atrace_verification("Question?", "Anime")
    assert trace["final_response"] == "baseline"
    assert trace["verifications"] == []
