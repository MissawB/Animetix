import pytest
from adapters.inference.local_text_adapter import LocalTextAdapter

def test_local_text_adapter_health_check():
    adapter = LocalTextAdapter()
    health = adapter.health_check()
    assert health["engine"] == "local_text"
