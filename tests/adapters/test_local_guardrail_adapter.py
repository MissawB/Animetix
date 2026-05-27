import pytest
from adapters.inference.local_guardrail_adapter import LocalGuardrailAdapter

def test_local_guardrail_adapter_health_check():
    adapter = LocalGuardrailAdapter()
    health = adapter.health_check()
    assert health["engine"] == "local_guardrail"
