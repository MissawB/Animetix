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
    # Chatbot / RAG / companion (~1 short LLM call)
    "chatbot_rag": 0.0018,
    "companion": 0.0018,
    # Graph & speech quick ops (~2–3 short calls)
    "graph_exploration": 0.0035,
    "speech_to_speech": 0.0035,
    # Medium inference: image analysis, manga ops, Singularity light
    "singularity_compile": 0.0075,
    "singularity_plasticity": 0.0075,
    "singularity_quantum": 0.0075,
    "manga_cleaner": 0.0075,
    "manga_translator": 0.0075,
    # Voice ingestion (transcription + indexing)
    "voice_ingestion": 0.0115,
    # Heavy multi-step inference
    "archetypist_fusion": 0.019,
    "soundscape": 0.019,
    "singularity_evolve": 0.019,
    "singularity_swarm": 0.019,
    # GPU-intensive single-output generation
    "forge_vn": 0.0387,
    "singularity_multiverse": 0.0387,
    "voice_cloning": 0.0387,
    # Very heavy: 3-D lift / long diffusion
    "image_to_3d": 0.058,
    # Flagship: full-length audio dubbing
    "voice_lab": 0.0771,
    # 3-D reconstruction / style-transfer at full resolution
    "fatezero": 0.1932,
    "cinematic_3d": 0.1932,
}

FEATURE_BX_COSTS: dict[str, int] = {
    key: bx_cost_for_usd(usd) for key, usd in FEATURE_COMPUTE_USD.items()
}
