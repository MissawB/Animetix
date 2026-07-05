from typing import List, Optional


class DjangoDriftBaselineStore:
    """Persiste les baselines de dérive (normes des embeddings) dans la table
    ``DriftBaseline`` — stockage partagé et durable, contrairement au FS local
    éphémère de Cloud Run."""

    def load(self, collection_name: str) -> Optional[List[float]]:
        from animetix.models import DriftBaseline  # noqa: E402

        row = DriftBaseline.objects.filter(collection_name=collection_name).first()
        return row.norms if row else None

    def save(self, collection_name: str, norms: List[float], sample_size: int) -> None:
        from animetix.models import DriftBaseline  # noqa: E402

        DriftBaseline.objects.update_or_create(
            collection_name=collection_name,
            defaults={"norms": norms, "sample_size": sample_size},
        )
