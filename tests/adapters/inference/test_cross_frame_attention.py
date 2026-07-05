from unittest.mock import MagicMock

import torch
from adapters.inference.image_gen_mixin import CrossFrameAttentionProcessor


def test_cross_frame_attention_processor_call():
    processor = CrossFrameAttentionProcessor(unet_chunk_size=2)

    # Mock attn object
    attn = MagicMock()
    mock_processor = MagicMock()
    attn.processor = mock_processor

    # Create dummy hidden_states [batch, sequence, channels]
    batch_size = 2
    sequence_length = 10
    channels = 32
    hidden_states = torch.randn(batch_size, sequence_length, channels)

    # Call processor
    processor(attn, hidden_states)

    # Verify that mock_processor was called
    assert mock_processor.called

    # Verify arguments passed to __call__
    args, kwargs = mock_processor.call_args
    # hidden_states should be passed as is
    assert torch.equal(args[1], hidden_states)

    # encoder_hidden_states should have been modified (concatenated with anchor frame)
    modified_encoder_hidden_states = args[2]
    assert modified_encoder_hidden_states.shape == (
        batch_size,
        sequence_length * 2,
        channels,
    )

    # First half should be original hidden_states
    assert torch.equal(
        modified_encoder_hidden_states[:, :sequence_length, :], hidden_states
    )

    # Second half should be anchor frame (first frame repeated for batch)
    anchor_frame = hidden_states[0:1].expand(batch_size, -1, -1)
    assert torch.equal(
        modified_encoder_hidden_states[:, sequence_length:, :], anchor_frame
    )
