"""Tests d'isolation de DriftService : fonctionne avec un VectorStorePort et un
ConfigPort injectés, sans Django ni la couche pipeline."""

from pathlib import Path

from core.ports.config_port import ConfigPort
from core.ports.vector_store_port import VectorStorePort


class _FakeConfig(ConfigPort):
    def __init__(self, base_dir: Path):
        self._base = base_dir

    def get(self, key, default=None):
        return self._base if key == "BASE_DIR" else default


class _FakeVectorStore(VectorStorePort):
    def __init__(self, embeddings):
        self._embeddings = embeddings

    def get_embeddings(self, collection_name, limit):
        return self._embeddings[:limit]

    def search_by_vector(self, collection_name, query_vector, limit=10):
        return []


def test_drift_service_uses_injected_ports(tmp_path):
    from core.domain.services.drift_service import DriftService

    # config.get("BASE_DIR").parent.parent -> tmp_path ; on ajoute 2 niveaux.
    base_dir = tmp_path / "lvl1" / "lvl2"
    base_dir.mkdir(parents=True)

    svc = DriftService(
        vector_store=_FakeVectorStore([[0.1, 0.2], [0.3, 0.4]]),
        config_port=_FakeConfig(base_dir),
    )
    assert svc.baseline_dir == tmp_path / "data" / "artifacts" / "baselines"
    assert svc.baseline_dir.exists()


def test_drift_service_reports_unknown_without_baseline(tmp_path):
    from core.domain.services.drift_service import DriftService

    base_dir = tmp_path / "a" / "b"
    base_dir.mkdir(parents=True)
    svc = DriftService(
        vector_store=_FakeVectorStore([]),
        config_port=_FakeConfig(base_dir),
    )
    result = svc.check_collection_drift("anime")
    assert result["status"] == "unknown"
