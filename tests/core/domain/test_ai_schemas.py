import pytest
from pydantic import ValidationError

def test_inference_response_schema():
    # Attempt to import the new schemas (should fail until implemented)
    from backend.core.domain.entities.ai_schemas import InferenceResponse, TokenLogProb
    
    res = InferenceResponse(
        text="Luffy", 
        metadata={"logprobs": [{"token": "Luffy", "logprob": -0.01}]}
    )
    assert res.text == "Luffy"
    assert res.metadata.logprobs[0].token == "Luffy"
    assert res.metadata.logprobs[0].logprob == -0.01
