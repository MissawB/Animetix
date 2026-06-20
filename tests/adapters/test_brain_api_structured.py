from unittest.mock import patch

from adapters.inference.brain_api_adapter import BrainAPIAdapter
from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int


def test_brain_api_generate_structured_success():
    adapter = BrainAPIAdapter(api_url="http://brain-api:5000")

    # The structured generation path produces raw text (here valid JSON) and
    # validates it against the Pydantic response model.
    with patch.object(
        adapter, "generate", return_value='{"name": "Test User", "age": 25}'
    ) as mock_generate:
        result = adapter.generate_structured(
            prompt="Extract user info", response_model=User
        )

    assert result == User(name="Test User", age=25)
    mock_generate.assert_called_once()
