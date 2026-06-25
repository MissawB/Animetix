import pytest
from core.domain.entities.ai_schemas import InferenceResponse
from core.ports.inference_port import InferencePort


class FakeSyncAdapter(InferencePort):
    def generate(self, prompt, system_prompt="sys", **kwargs):
        return InferenceResponse(text="sync")

    def get_text_embedding(self, text):
        return []

    def health_check(self):
        return {"status": "online"}

    def stream_generate(self, prompt, system_prompt="sys", **kwargs):
        yield InferenceResponse(text="chunk1")
        yield InferenceResponse(text="chunk2")


@pytest.mark.asyncio
async def test_inference_port_astream_generate_wraps_sync():
    adapter = FakeSyncAdapter()
    chunks = []
    async for chunk in adapter.astream_generate("Q"):
        chunks.append(chunk.text)
    assert chunks == ["chunk1", "chunk2"]


@pytest.mark.asyncio
async def test_brain_api_adapter_astream_generate_native():
    from unittest.mock import AsyncMock, MagicMock, patch

    from adapters.inference.brain_api_adapter import BrainAPIAdapter

    adapter = BrainAPIAdapter(api_url="http://brain:5000", api_key="dev-key")

    async def fake_aiter_text():
        for chunk in ["a", "b", "c"]:
            yield chunk

    mock_response = MagicMock()
    mock_response.aiter_text.side_effect = fake_aiter_text

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_ctx
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch(
        "adapters.inference.brain_api_adapter.httpx.AsyncClient",
        return_value=mock_client,
    ):
        chunks = []
        async for chunk in adapter.astream_generate("Q"):
            chunks.append(chunk.text)

    assert chunks == ["a", "b", "c"]
    mock_client.stream.assert_called_once()
    args, kwargs = mock_client.stream.call_args
    assert args == ("POST", "http://brain:5000/stream_generate")
    assert kwargs["json"]["prompt"] == "Q"


@pytest.mark.asyncio
async def test_unified_astream_generate_native():
    import json as _json
    from unittest.mock import AsyncMock, MagicMock, patch

    from adapters.inference.unified_inference_adapter import UnifiedInferenceAdapter

    adapter = UnifiedInferenceAdapter(
        api_base="http://llm:8000/v1", model_name="m", api_key="k"
    )

    lines = [
        "data: " + _json.dumps({"choices": [{"delta": {"content": "Hel"}}]}),
        "data: " + _json.dumps({"choices": [{"delta": {"content": "lo"}}]}),
        "data: [DONE]",
    ]

    async def fake_aiter_lines():
        for ln in lines:
            yield ln

    mock_response = MagicMock()
    mock_response.aiter_lines.side_effect = fake_aiter_lines
    mock_response.raise_for_status.return_value = None

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock()

    mock_client = MagicMock()
    mock_client.stream.return_value = mock_stream_ctx
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with (
        patch(
            "adapters.inference.unified_inference_adapter.httpx.AsyncClient",
            return_value=mock_client,
        ),
        patch(
            "adapters.inference.unified_inference_adapter.is_safe_url",
            return_value=True,
        ),
    ):
        chunks = []
        async for c in adapter.astream_generate("Q", include_logprobs=False):
            chunks.append(c.text)

    assert chunks == ["Hel", "lo"]
    mock_client.stream.assert_called_once()
    args, kwargs = mock_client.stream.call_args
    assert args[0] == "POST"
    assert kwargs["json"]["stream"] is True
    assert adapter._last_completion == "Hello"


@pytest.mark.asyncio
async def test_google_genai_astream_generate_native(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock, patch

    from adapters.inference.google_genai_adapter import GoogleGenAIAdapter

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def _chunk(text):
        c = MagicMock()
        c.text = text
        c.candidates = []
        c.usage_metadata = None
        return c

    async def fake_stream():
        for t in ["Foo", "Bar"]:
            yield _chunk(t)

    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content_stream = AsyncMock(return_value=fake_stream())

    with patch(
        "adapters.inference.google_genai_adapter.genai.Client", return_value=client
    ):
        adapter = GoogleGenAIAdapter(api_key="key")

    chunks = []
    async for c in adapter.astream_generate("Q"):
        chunks.append(c.text)

    assert chunks == ["Foo", "Bar"]
    client.aio.models.generate_content_stream.assert_awaited_once()
