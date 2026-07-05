"""Tests d'isolation de DriftService : les baselines (normes des embeddings)
sont persistées via un store injecté (DB Django en réel)."""

from core.ports.vector_store_port import VectorStorePort


class _FakeVectorStore(VectorStorePort):
    def __init__(self, embeddings):
        self._embeddings = embeddings

    def get_embeddings(self, collection_name, limit):
        return self._embeddings[:limit]

    def search_by_vector(self, collection_name, query_vector, limit=10):
        return []


class _FakeStore:
    """Store de baselines en mémoire (API load/save du store DB)."""

    def __init__(self):
        self.data = {}

    def load(self, collection_name):
        return self.data.get(collection_name)

    def save(self, collection_name, norms, sample_size):
        self.data[collection_name] = norms


def test_reports_unknown_without_baseline():
    from core.domain.services.drift_service import DriftService

    svc = DriftService(
        vector_store=_FakeVectorStore([[0.1, 0.2], [0.3, 0.4]]),
        baseline_store=_FakeStore(),
    )
    assert svc.check_collection_drift("anime")["status"] == "unknown"


def test_generate_baseline_persists_and_enables_real_ks_test():
    from core.domain.services.drift_service import DriftService

    vectors = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]
    store = _FakeStore()
    svc = DriftService(vector_store=_FakeVectorStore(vectors), baseline_store=store)

    svc.generate_new_baseline("anime")
    assert "anime" in store.data
    assert len(store.data["anime"]) == len(vectors)  # one norm per vector

    report = svc.check_collection_drift("anime")
    # Baseline == état courant → distributions identiques → pas de dérive.
    assert report["status"] == "healthy"
    assert report["p_value"] is not None
    assert report["sample_size"] == len(vectors)


def test_generate_baseline_noop_on_empty_collection():
    from core.domain.services.drift_service import DriftService

    store = _FakeStore()
    svc = DriftService(vector_store=_FakeVectorStore([]), baseline_store=store)
    svc.generate_new_baseline("manga")
    assert store.data == {}


def test_get_drift_report_covers_all_collections():
    from core.domain.services.drift_service import DriftService

    svc = DriftService(vector_store=_FakeVectorStore([]), baseline_store=_FakeStore())
    report = svc.get_drift_report()
    assert set(report.keys()) == {"anime", "manga", "character"}
