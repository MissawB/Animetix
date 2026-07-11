"""
Single source of truth for the local (self-hosted) model ids used across
Animetix. Each role is env-overridable; centralizing here resolves the
divergent hardcoded defaults (LLM llama3 vs qwen3.5; text Qwen2.5-1.5B vs
Qwen3.5-4B). Pure module — only `os`.
"""

import os

LLM_OLLAMA_MODEL = os.getenv("LLM_MODEL_NAME", "qwen3.5:9b")
LOCAL_TEXT_MODEL = os.getenv("LOCAL_MODEL_ID", "Qwen/Qwen3.5-9B")
DRAFT_TEXT_MODEL = os.getenv("DRAFT_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
COMPACT_REASONING_MODEL = os.getenv("COMPACT_MODEL_ID", "WeiboAI/VibeThinker-3B")
LOCAL_DIFFUSION_MODEL_ID = os.getenv(
    "LOCAL_DIFFUSION_MODEL", "black-forest-labs/FLUX.1-schnell"
)
# Default multimodal VLM (image understanding) served by the local/brain stack.
LOCAL_VLM_MODEL = os.getenv("LOCAL_VLM_MODEL_ID", "Qwen/Qwen3-VL-30B-A3B-Instruct")
# Lighter VLM used for temporal/video analysis.
LOCAL_VIDEO_VLM_MODEL = os.getenv(
    "LOCAL_VIDEO_VLM_MODEL_ID", "Qwen/Qwen3-VL-8B-Instruct"
)
# Small student model for distillation and RL/DPO training runs.
SMALL_TRAINABLE_MODEL = os.getenv("SMALL_TRAINABLE_MODEL_ID", "Qwen/Qwen3-0.6B")
# Cross-encoder used by RerankComponent (revision pinned in model_registry).
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-12-v2")
# SentenceTransformer used by LocalTextAdapter.get_text_embedding.
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL_ID", "all-MiniLM-L6-v2")
