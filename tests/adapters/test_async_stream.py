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
