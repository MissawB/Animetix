from unittest.mock import MagicMock
from backend.core.domain.services.neuromorphic_plasticity_service import (
    SynapticPlasticityService,
)


def test_plasticity_service_integration():
    mock_inference = MagicMock()
    # This instantiation should fail because SynapticPlasticityService doesn't accept inference_engine
    service = SynapticPlasticityService(inference_engine=mock_inference)
    # Trigger interaction and verify mock
    service.apply_plasticity(data={})
    assert mock_inference.run.called
