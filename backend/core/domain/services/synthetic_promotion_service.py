# -*- coding: utf-8 -*-
import logging
from typing import Dict, Any
from core.ports.gold_dataset_port import GoldDatasetPort

logger = logging.getLogger("animetix.mlops.promotion")


class SyntheticDataPromotionService:
    """
    Service d'orchestration HITL : Pousse les données synthétiques validées
    vers leurs destinations finales (Neo4j, Datasets FT, etc.).
    """

    def __init__(
        self,
        gold_dataset_port: GoldDatasetPort,
        domain_synthesizer=None,
        star_mlops_service=None,
    ):
        self.gold_dataset_port = gold_dataset_port
        self.domain_synthesizer = domain_synthesizer
        self.star_mlops_service = star_mlops_service

    def promote_validated_entries(self) -> Dict[str, int]:
        """
        Scanne les entrées validées et les distribue selon leur type.
        """
        entries = self.gold_dataset_port.get_unprocessed_validated_entries()
        if not entries:
            logger.info("No validated entries to promote.")
            return {"promoted": 0}

        stats = {"MULTIVERSE": 0, "QA": 0, "DISTILLATION": 0, "OTHER": 0}
        processed_ids = []

        for entry in entries:
            entry_type = entry.get("entry_type", "QA")
            success = False

            if entry_type == "MULTIVERSE":
                success = self._promote_multiverse(entry)
            elif entry_type in ["QA", "DISTILLATION"]:
                # Ces types sont gérés par le StarMLOpsDomainService lors de l'export global
                # On les laisse dans la queue de promotion pour l'instant ou on les marque
                # pour export.
                success = True  # Marqué comme prêt pour export
            else:
                logger.warning(f"Unknown entry type for promotion: {entry_type}")
                success = True  # On évite de bloquer, mais on ne fait rien

            if success:
                stats[entry_type] = stats.get(entry_type, 0) + 1
                processed_ids.append(entry["id"])

        # Si on a des données de type QA/DISTILLATION, on peut déclencher l'export STaR
        if stats["QA"] > 0 or stats["DISTILLATION"] > 0:
            if self.star_mlops_service:
                self.star_mlops_service.prepare_star_dataset()

        # Nettoyage de la DB pour les entrées traitées
        if processed_ids:
            self.gold_dataset_port.mark_entries_as_processed(processed_ids)

        total = sum(stats.values())
        logger.info(
            f"✅ Promotion complete: {total} entries processed. Breakdown: {stats}"
        )
        return {"promoted": total, "details": stats}

    def _promote_multiverse(self, entry: Dict[str, Any]) -> bool:
        """Pousse un univers synthétique validé vers Neo4j."""
        if not self.domain_synthesizer:
            logger.error("DomainSynthesizer missing for MULTIVERSE promotion.")
            return False

        universe_data = entry.get("metadata")
        if not universe_data:
            logger.error(f"Missing universe metadata in entry {entry['id']}")
            return False

        return self.domain_synthesizer._execute_graph_persistence(universe_data)
