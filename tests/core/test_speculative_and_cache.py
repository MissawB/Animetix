import os
from unittest.mock import MagicMock, patch

import torch
from adapters.inference.local_text_adapter import LocalTextAdapter


@patch("adapters.inference.local_text_adapter.lazy_import")
def test_local_text_adapter_speculative_and_cache(mock_lazy):
    # Mock torch and transformers to bypass actual GPU loading
    mock_torch = MagicMock()
    mock_tf = MagicMock()

    def side_effect(name):
        if name == "torch":
            return mock_torch
        if name == "transformers":
            return mock_tf
        return MagicMock()

    mock_lazy.side_effect = side_effect

    # Instantiate adapter with speculative decoding env variables
    os.environ["SPECULATIVE_DECODING"] = "True"
    os.environ["DRAFT_MODEL_ID"] = "Qwen/Qwen2.5-0.5B-Instruct"

    adapter = LocalTextAdapter(model_id="Qwen/Qwen2.5-1.5B-Instruct")

    # Mock the models and tokenizers
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    mock_tokenizer.decode.return_value = "Response content"

    mock_model = MagicMock()
    mock_model.device = "cpu"

    # Mock model.generate to return outputs containing sequences and past_key_values
    mock_gen_output = MagicMock()
    mock_gen_output.sequences = torch.tensor(
        [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]]
    )
    # Mock a past_key_values tuple
    mock_gen_output.past_key_values = ((torch.randn(1, 2, 3),),)
    mock_model.generate.return_value = mock_gen_output

    adapter.tokenizer = mock_tokenizer
    adapter.model = mock_model
    adapter.draft_model = MagicMock()
    adapter.radix_cache = MagicMock()

    # 1. Test cache miss
    adapter.radix_cache.query.return_value = (None, 0)
    response = adapter.generate("prompt query here")

    assert response.text == "Response content"
    # Should call model.generate with input_ids and assistant_model
    mock_model.generate.assert_called()
    kwargs = mock_model.generate.call_args[1]
    assert "assistant_model" in kwargs

    # 2. Test cache hit
    mock_pkv = ((torch.randn(1, 2, 3),),)
    adapter.radix_cache.query.return_value = (mock_pkv, 6)
    response_hit = adapter.generate("prompt query here")
    assert response_hit.text == "Response content"

    # Verify correct suffix position ids and past_key_values are passed
    kwargs_hit = mock_model.generate.call_args[1]
    assert "past_key_values" in kwargs_hit
    assert "position_ids" in kwargs_hit
    assert "attention_mask" in kwargs_hit
