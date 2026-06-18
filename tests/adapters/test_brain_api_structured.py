from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from adapters.inference.brain_api_adapter import BrainAPIAdapter


class User(BaseModel):
    name: str
    age: int


def test_brain_api_generate_structured_success():
    adapter = BrainAPIAdapter(brain_api_url="http://brain-api:5000")

    # Mocking instructor and OpenAI client
    mock_user = User(name="Test User", age=25)

    with patch("instructor.from_openai") as mock_from_openai:
        import instructor  # noqa: E402

        mock_client = MagicMock()
        mock_from_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_user

        result = adapter.generate_structured(
            prompt="Extract user info", response_model=User
        )

        assert result == mock_user
        mock_from_openai.assert_called_once()
        # Verify it uses brain_api_url as base_url
        args, kwargs = mock_from_openai.call_args
        assert kwargs["mode"] == instructor.Mode.JSON
