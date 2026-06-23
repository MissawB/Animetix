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
