"""Tests d'isolation de DriftService : les baselines sont persistées via un
stockage injecté (Django default_storage en réel — GCS prod / FS dev)."""

import io

from core.ports.vector_store_port import VectorStorePort


class _FakeVectorStore(VectorStorePort):
    def __init__(self, embeddings):
        self._embeddings = embeddings

    def get_embeddings(self, collection_name, limit):
        return self._embeddings[:limit]

    def search_by_vector(self, collection_name, query_vector, limit=10):
        return []


class _FakeStorage:
    """Stockage en mémoire imitant l'API Django Storage utilisée par le service."""

    def __init__(self):
        self.files = {}

    def exists(self, name):
        return name in self.files

    def open(self, name, mode="rb"):
        return io.BytesIO(self.files[name])

    def save(self, name, content):
        self.files[name] = content.read()
        return name

    def delete(self, name):
        self.files.pop(name, None)


def test_reports_unknown_without_baseline():
    from core.domain.services.drift_service import DriftService

    svc = DriftService(
        vector_store=_FakeVectorStore([[0.1, 0.2], [0.3, 0.4]]),
        storage=_FakeStorage(),
    )
    assert svc.check_collection_drift("anime")["status"] == "unknown"


def test_generate_baseline_persists_and_enables_real_ks_test():
    from core.domain.services.drift_service import DriftService

    vectors = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8], [0.9, 1.0]]
    storage = _FakeStorage()
    svc = DriftService(vector_store=_FakeVectorStore(vectors), storage=storage)

    svc.generate_new_baseline("anime")
    assert storage.exists("drift-baselines/anime_baseline.npy")

    report = svc.check_collection_drift("anime")
    # Baseline == état courant → distributions identiques → pas de dérive.
    assert report["status"] == "healthy"
    assert report["p_value"] is not None
    assert report["sample_size"] == len(vectors)


def test_generate_baseline_noop_on_empty_collection():
    from core.domain.services.drift_service import DriftService

    storage = _FakeStorage()
    svc = DriftService(vector_store=_FakeVectorStore([]), storage=storage)
    svc.generate_new_baseline("manga")
    assert not storage.exists("drift-baselines/manga_baseline.npy")


def test_get_drift_report_covers_all_collections():
    from core.domain.services.drift_service import DriftService

    svc = DriftService(vector_store=_FakeVectorStore([]), storage=_FakeStorage())
    report = svc.get_drift_report()
    assert set(report.keys()) == {"anime", "manga", "character"}
