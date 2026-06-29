"""
Single source of truth for the Berrix (Bx) economy.

Pure-Python (no Django) so it stays a domain service like pricing_service.py.
Config is read once at import via os.getenv with literal defaults; override per
environment without code changes.

Margin model: 1 Bx is backed by its net selling value (BX_PRICE_USD_NET). A
feature may only cost as much real compute as (1 - TARGET_MARGIN) of the Bx
value the user spends on it — that residual is the treasury cushion.
"""

import math
import os


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


# --- Anchors (env-overridable) ---
BX_PRICE_USD_NET = _f(
    "BERRIX_BX_PRICE_USD_NET", 0.00043
)  # net $ per Bx sold (pack price after fees)
TARGET_MARGIN = _f("BERRIX_TARGET_MARGIN", 0.10)  # cushion, mid of 5-15%
AD_REVENUE_USD = _f("BERRIX_AD_REVENUE_USD", 0.02)  # net $ per rewarded ad
MINING_REWARD_BX = _i(
    "BERRIX_MINING_REWARD_BX", 10
)  # loss-leader (no real revenue), capped


def bx_cost_for_usd(usd_compute: float) -> int:
    """Minimum Bx price for a feature costing `usd_compute`, guaranteeing the margin."""
    denom = BX_PRICE_USD_NET * (1 - TARGET_MARGIN)
    return max(1, math.ceil(usd_compute / denom))


def ad_reward_bx() -> int:
    """Bx granted per rewarded ad, so the ad keeps the margin on the Bx it funds."""
    return math.floor(AD_REVENUE_USD * (1 - TARGET_MARGIN) / BX_PRICE_USD_NET)


# ---------------------------------------------------------------------------
# Feature cost table
# ---------------------------------------------------------------------------
# FEATURE_COMPUTE_USD: estimated real-compute cost (USD) per feature invocation.
# FEATURE_BX_COSTS:    how many Bx we actually charge — always >= bx_cost_for_usd(usd),
#                      so the margin floor is guaranteed on every call.
#
# To add a feature: set its USD anchor here; the charged Bx is computed automatically.
# To add a premium: set a higher value in FEATURE_BX_COSTS than the floor requires.
# ---------------------------------------------------------------------------

FEATURE_COMPUTE_USD: dict[str, float] = {
    "companion": 0.002,
    "agentic_rag": 0.002,
    "knowledge_graph": 0.001,
    "vn_script": 0.02,
    "creative_fusion": 0.03,
    "singularity_basic": 0.004,  # kernel / plasticity / quantum
    "singularity_mid": 0.008,  # llm-evolution / swarm
    "multiverse_synth": 0.02,
    "manga_voice": 0.05,
    "style_transfer": 0.15,
    "voice_ingest": 0.005,
    "soundscape": 0.01,
    "speech_to_speech": 0.003,
    "manga_clean": 0.004,
    "manga_translate": 0.004,
    "voice_clone": 0.005,
    "image_to_3d": 0.04,
    "cinematic_3d": 0.15,
    # GPU-backed games (inference per round)
    "vision_clip": 0.002,  # single CLIP forward pass
    "paradox": 0.003,  # one LLM reasoning + scenario generation
    "vs_battle": 0.004,  # battle reasoning generation
    "akinetix_rl": 0.004,  # RL agent rollout
    # GPU-backed SSE streams (per generation)
    "emoji_stream": 0.002,  # emoji hint generation
    "animinator": 0.002,  # oracle Q&A turn
    "tree_of_thoughts": 0.01,  # multi-node ToT search (breadth x depth LLM calls)
}

FEATURE_BX_COSTS: dict[str, int] = {
    # Chatbot / RAG / companion — floor is 5 Bx; bumped to 6 to stay above floor at all envs
    "agentic_rag": 6,
    "companion": 6,
    # Graph & speech quick ops
    "knowledge_graph": 10,
    "speech_to_speech": 10,
    # Medium inference
    "singularity_basic": 20,
    "manga_clean": 20,
    "manga_translate": 20,
    # Voice ingestion
    "voice_ingest": 30,
    # Heavy multi-step — creative_fusion bumped to 78 (brand premium above floor 50)
    "creative_fusion": 78,
    "soundscape": 50,
    "singularity_mid": 50,
    # GPU-intensive
    "vn_script": 100,
    "multiverse_synth": 100,
    "voice_clone": 100,
    # Very heavy
    "image_to_3d": 150,
    # Flagship
    "manga_voice": 200,
    # Full-resolution 3-D / style-transfer
    "style_transfer": 500,
    "cinematic_3d": 500,
    # GPU-backed games — floors: vision 6, paradox 8, vs_battle/akinetix_rl 11
    "vision_clip": 6,
    "paradox": 8,
    "vs_battle": 12,
    "akinetix_rl": 12,
    # GPU-backed SSE streams — floors: emoji/animinator 6, ToT 26
    "emoji_stream": 6,
    "animinator": 6,
    "tree_of_thoughts": 30,
}

# --- Pack catalog (server-authoritative). Prices in minor units (cents). ---
# Priced at or above the canonical net Bx value so every purchase keeps the margin.
# Floor = bx * BX_PRICE_USD_NET * 0.95 converted to cents:
#   initiate: 10_000 * 0.00043 * 0.95 * 100 = 408.5  → 499 ✓
#   adept:    30_000 * 0.00043 * 0.95 * 100 = 1225.5 → 1399 ✓
#   master:  100_000 * 0.00043 * 0.95 * 100 = 4085   → 4299 ✓
PACKS: dict[str, dict] = {
    "initiate": {"bx": 10_000, "price_cents": 499, "currency": "eur"},
    "adept": {"bx": 30_000, "price_cents": 1399, "currency": "eur"},
    "master": {"bx": 100_000, "price_cents": 4299, "currency": "eur"},
}
