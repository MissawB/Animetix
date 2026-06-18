from adapters.inference.local_rerank_adapter import LocalRerankAdapter


def test_local_rerank_adapter_health_check():
    adapter = LocalRerankAdapter()
    health = adapter.health_check()
    assert health["engine"] == "local_rerank"
