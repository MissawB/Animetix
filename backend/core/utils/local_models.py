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
