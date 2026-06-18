import pytest
from pydantic import ValidationError

from backend.api.animetix.schemas import OfflineSyncSchema


def test_offline_sync_schema_valid():
    data = [{"game_mode": "classic", "score": 100, "attempts": 1}]
    schema = OfflineSyncSchema.model_validate(data)
    assert len(schema.root) == 1


def test_offline_sync_schema_invalid_mode():
    data = [{"game_mode": "fictif", "score": 100}]
    with pytest.raises(ValidationError):
        OfflineSyncSchema.model_validate(data)
