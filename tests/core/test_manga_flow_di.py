from animetix.containers import get_container
from adapters.inference.fallback_adapter import FallbackInferenceAdapter


def test_manga_flow_service_wires_fallback_engine():
    # Chargement du conteneur réel
    container = get_container()
    manga_service = container.core.manga_flow_service()

    # Valider que le moteur injecté est bien FallbackInferenceAdapter
    assert isinstance(manga_service.inference_engine, FallbackInferenceAdapter)
