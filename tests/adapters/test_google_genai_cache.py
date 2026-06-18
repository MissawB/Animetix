import os
import time
from unittest.mock import MagicMock, patch

import pytest
from adapters.inference.google_genai_adapter import GoogleGenAIAdapter


# Mock response structure for the SDK call
def make_mock_generate_response():
    mock_res = MagicMock()
    mock_res.text = "Mocked Response"
    mock_res.candidates = []
    # Usage metadata
    mock_res.usage_metadata = MagicMock()
    mock_res.usage_metadata.prompt_token_count = 10
    mock_res.usage_metadata.candidates_token_count = 5
    mock_res.usage_metadata.total_token_count = 15
    return mock_res


@pytest.fixture
def mock_genai_client(mocker):
    # Mock client and its sub-interfaces
    mock_client = MagicMock()
    mock_models = MagicMock()
    mock_caches = MagicMock()

    mock_client.models = mock_models
    mock_client.caches = mock_caches

    # generate_content return mock
    mock_models.generate_content.return_value = make_mock_generate_response()

    # caches.create return mock
    mock_cache_object = MagicMock()
    mock_cache_object.name = "cachedContents/mock-cache-id-12345"
    mock_caches.create.return_value = mock_cache_object

    mocker.patch("google.genai.Client", return_value=mock_client)
    return mock_client


def test_cache_not_triggered_below_threshold(mock_genai_client, mocker):
    # Set threshold to 100 characters for test purposes
    with patch.dict(
        os.environ,
        {"GEMINI_CACHE_THRESHOLD": "100", "GEMINI_MODEL_NAME": "gemini-3.5-flash"},
    ):
        adapter = GoogleGenAIAdapter(api_key="fake-key")

        # System prompt is 30 characters (below threshold of 100)
        system_prompt = "Tu es un assistant simple."
        prompt = "Bonjour"

        adapter.generate(prompt, system_prompt=system_prompt)

        # Verify no cache creation was called
        mock_genai_client.caches.create.assert_not_called()

        # Verify system_instruction was passed in config
        mock_genai_client.models.generate_content.assert_called_once()
        call_args = mock_genai_client.models.generate_content.call_args[1]
        assert call_args["model"] == "gemini-3.5-flash"
        assert call_args["contents"] == prompt
        assert call_args["config"].system_instruction == system_prompt
        assert (
            not hasattr(call_args["config"], "cached_content")
            or call_args["config"].cached_content is None
        )


def test_cache_created_and_used_above_threshold(mock_genai_client, mocker):
    # Threshold set to 50 chars, system prompt set to 80 chars (above threshold)
    with patch.dict(
        os.environ,
        {
            "GEMINI_CACHE_THRESHOLD": "50",
            "GEMINI_CACHE_TTL": "120",
            "GEMINI_MODEL_NAME": "gemini-3.5-flash",
        },
    ):
        adapter = GoogleGenAIAdapter(api_key="fake-key")

        system_prompt = (
            "Tu es un expert Otaku très sage et instruit avec de grandes connaissances."
        )
        prompt = "Qui est Luffy ?"

        adapter.generate(prompt, system_prompt=system_prompt)

        # Verify client.caches.create was called with the correct parameters
        mock_genai_client.caches.create.assert_called_once()
        cache_call_config = mock_genai_client.caches.create.call_args[1]["config"]
        assert cache_call_config.system_instruction == system_prompt
        assert cache_call_config.ttl == "120s"

        # Verify generate_content was called using cached_content instead of system_instruction
        mock_genai_client.models.generate_content.assert_called_once()
        call_args = mock_genai_client.models.generate_content.call_args[1]
        assert (
            call_args["config"].cached_content == "cachedContents/mock-cache-id-12345"
        )
        assert call_args["config"].system_instruction is None


def test_cache_reuse_on_repeated_calls(mock_genai_client, mocker):
    with patch.dict(
        os.environ,
        {"GEMINI_CACHE_THRESHOLD": "50", "GEMINI_MODEL_NAME": "gemini-3.5-flash"},
    ):
        adapter = GoogleGenAIAdapter(api_key="fake-key")

        system_prompt = (
            "Tu es un expert Otaku très sage et instruit avec de grandes connaissances."
        )

        # First call
        adapter.generate("Prompt 1", system_prompt=system_prompt)
        # Second call with the same system prompt
        adapter.generate("Prompt 2", system_prompt=system_prompt)

        # Caches should only be created ONCE
        assert mock_genai_client.caches.create.call_count == 1
        # generate_content should be called twice
        assert mock_genai_client.models.generate_content.call_count == 2

        # Both calls must use the same cache name
        call1_config = mock_genai_client.models.generate_content.call_args_list[0][1][
            "config"
        ]
        call2_config = mock_genai_client.models.generate_content.call_args_list[1][1][
            "config"
        ]
        assert call1_config.cached_content == "cachedContents/mock-cache-id-12345"
        assert call2_config.cached_content == "cachedContents/mock-cache-id-12345"


def test_cache_expiration_and_deletion(mock_genai_client, mocker):
    with patch.dict(
        os.environ,
        {
            "GEMINI_CACHE_THRESHOLD": "50",
            "GEMINI_CACHE_TTL": "1",
            "GEMINI_MODEL_NAME": "gemini-3.5-flash",
        },
    ):
        adapter = GoogleGenAIAdapter(api_key="fake-key")

        system_prompt = (
            "Tu es un expert Otaku très sage et instruit avec de grandes connaissances."
        )

        # 1. First call creates cache
        adapter.generate("Prompt 1", system_prompt=system_prompt)
        assert mock_genai_client.caches.create.call_count == 1

        # Simulate time passing beyond expiration
        mocker.patch("time.time", return_value=time.time() + 10)

        # 2. Second call should detect expiration, delete the old cache, and create a new one
        adapter.generate("Prompt 2", system_prompt=system_prompt)

        # Delete should be called for the old cache name
        mock_genai_client.caches.delete.assert_called_once_with(
            name="cachedContents/mock-cache-id-12345"
        )

        # caches.create count should be 2 now
        assert mock_genai_client.caches.create.call_count == 2
