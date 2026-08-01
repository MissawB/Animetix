"""Vérification serveur (SSV) d'une récompense de pub *rewarded*.

Règle : une pub AdSense n'est JAMAIS le déclencheur d'une récompense. La
récompense Bx est financée par un réseau REWARDED dédié (Google Ad Manager
rewarded units, ou un SSP tiers) qui, à la fin d'une pub réellement visionnée,
émet un JETON SIGNÉ. Le serveur DOIT vérifier ce jeton avant de créditer —
sinon n'importe qui peut appeler l'endpoint et se créditer des Bx.

Modes :
- **stub** (aucun réseau configuré, `REWARDED_ADS_PROVIDER` absent/"stub") :
  dev — le front joue un minuteur d'engagement sans vraie pub, le crédit est
  autorisé SANS jeton.
- **réseau réel** (`REWARDED_ADS_PROVIDER` = un réseau) : un jeton signé valide
  devient OBLIGATOIRE ; tant que la vérification de signature n'est pas
  implémentée, on refuse par sécurité (fail-closed).
"""

import logging
import os

logger = logging.getLogger("animetix.billing")


def rewarded_ads_provider() -> str:
    """Réseau rewarded configuré (minuscules) ; "stub" si aucun."""
    return (os.getenv("REWARDED_ADS_PROVIDER") or "stub").strip().lower()


def verify_rewarded_ad(reward_token: str | None) -> bool:
    """True si la récompense peut être créditée.

    - mode stub : autorisé sans jeton (dev).
    - réseau réel : jeton signé valide OBLIGATOIRE (fail-closed sinon).
    """
    provider = rewarded_ads_provider()

    if provider in ("", "stub"):
        # Dev : pas de vraie pub → pas de SSV. On autorise le crédit.
        return True

    if not reward_token:
        logger.warning(
            "Rewarded credit refused: provider=%s mais aucun reward_token.", provider
        )
        return False

    # TODO(option A) : vérifier la signature du jeton auprès du réseau (SSV) —
    # p.ex. valider la signature Google Ad Manager, ou appeler l'API de
    # vérification du SSP. Tant que ce n'est pas implémenté, refuser (fail-closed)
    # pour ne jamais créditer sur un jeton non vérifié.
    logger.error(
        "Rewarded credit refused: provider=%s configuré mais SSV non implémentée.",
        provider,
    )
    return False
