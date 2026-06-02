# Implement Cross-Frame Attention Processor Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `CrossFrameAttentionProcessor` class in `backend/adapters/inference/diffusers_adapter.py` to maintain appearance consistency across frames.

**Architecture:** Add a helper class `CrossFrameAttentionProcessor` that modifies attention mechanism to look at the first frame as an anchor.

**Tech Stack:** Python, PyTorch (lazy_import), Diffusers.

---

### Task 1: Research and Setup

**Files:**
- Modify: `backend/adapters/inference/diffusers_adapter.py`

- [ ] **Step 1: Verify current imports and class structure**
Read the beginning of `backend/adapters/inference/diffusers_adapter.py` to ensure `torch` is correctly handled.

### Task 2: Implement CrossFrameAttentionProcessor

**Files:**
- Modify: `backend/adapters/inference/diffusers_adapter.py`

- [ ] **Step 1: Insert `CrossFrameAttentionProcessor` class**
Insert the class before `DiffusersAdapter`.

```python
class CrossFrameAttentionProcessor:
    """
    Processor for Cross-Frame Attention. 
    It forces the attention to look at the first frame (anchor) or across the batch 
    to maintain appearance consistency.
    """
    def __init__(self, unet_chunk_size=2):
        self.unet_chunk_size = unet_chunk_size

    def __call__(self, attn, hidden_states, encoder_hidden_states=None, attention_mask=None):
        batch_size, sequence_length, _ = hidden_states.shape
        # self.unet_chunk_size is usually the number of frames (or batch dimension)
        
        if encoder_hidden_states is None:
            # Self-attention: reshape to allow cross-frame interaction
            # We treat the hidden states as [frames, pixels, channels]
            # And force attention to the first frame or average
            encoder_hidden_states = hidden_states
        
        # Simple cross-frame logic: every frame attends to the first frame's features
        # to anchor the style and identity.
        if encoder_hidden_states is not None:
            # Reshape hidden_states to [batch/frames, pixels, channels]
            # Cross-frame: use the first frame as anchor for all frames in batch
            anchor_frame = encoder_hidden_states[0:1].expand(batch_size, -1, -1)
            encoder_hidden_states = torch.cat([encoder_hidden_states, anchor_frame], dim=1)

        return attn.processor.__call__(attn, hidden_states, encoder_hidden_states, attention_mask)
```

### Task 3: Verification

**Files:**
- Create: `tests/adapters/inference/test_cross_frame_attention.py`

- [ ] **Step 1: Write a basic test for the processor**
Create a test that mocks `attn` and `hidden_states` to verify the logic.

- [ ] **Step 2: Run the test**
Run: `pytest tests/adapters/inference/test_cross_frame_attention.py`
Expected: PASS

- [ ] **Step 3: Syntax check the main file**
Run: `python -m py_compile backend/adapters/inference/diffusers_adapter.py`
Expected: No errors.

### Task 4: Commit

- [ ] **Step 1: Commit the changes**

```bash
git add backend/adapters/inference/diffusers_adapter.py tests/adapters/inference/test_cross_frame_attention.py
git commit -m "feat: implement CrossFrameAttentionProcessor for temporal consistency"
```
