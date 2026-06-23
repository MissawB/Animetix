import json
import logging
import os

from django.core.management.base import BaseCommand

from animetix.containers import get_container

logger = logging.getLogger("animetix.ablation")

METRICS = ["faithfulness", "answer_relevancy", "context_precision"]


class Command(BaseCommand):
    help = (
        "Ablation: run the RAG pipeline with cognitive boosters ON vs OFF and "
        "report RAGAS deltas (faithfulness / answer_relevancy / context_precision)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source", choices=["curated", "gold"], default="curated")
        parser.add_argument("--media-type", default="Anime")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **options):
        container = get_container()
        rag = container.agentic.rag_service()
        judge = container.core.ragas_eval_service()

        queries = self._load_queries(
            options["source"], options["media_type"], container
        )
        if options["limit"]:
            queries = queries[: options["limit"]]
        if not queries:
            self.stdout.write(self.style.WARNING("No queries to evaluate."))
            return

        agg = {"OFF": {}, "ON": {}}
        skipped = 0
        for item in queries:
            query = item["query"]
            media_type = item.get("media_type", options["media_type"])
            try:
                row = self._eval_both(rag, judge, query, media_type)
            except Exception as e:  # one bad query must not abort the run
                logger.warning(f"Skipped '{query}': {e}")
                skipped += 1
                continue
            for mode in ("OFF", "ON"):
                for metric, value in row[mode].items():
                    agg[mode].setdefault(metric, []).append(value)

        self._render(agg, len(queries), skipped)

    def _eval_both(self, rag, judge, query, media_type):
        result = {}
        for mode, enabled in (("OFF", False), ("ON", True)):
            rag.set_cognitive_boosters(enabled)
            answer, context = rag.generate_advanced_answer_with_context(
                query, media_type
            )
            result[mode] = judge.evaluate_response(query, context, answer)
        return result

    def _load_queries(self, source, media_type, container):
        if source == "gold":
            entries = container.persistence.gold_dataset_adapter().get_all_entries()
            return [
                {"query": e.get("question", ""), "media_type": media_type}
                for e in entries
                if e.get("question")
            ]
        path = os.path.join(
            os.path.dirname(__file__), "data", "rag_ablation_queries.json"
        )
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _render(self, agg, total, skipped):
        def mean(xs):
            return sum(xs) / len(xs) if xs else 0.0

        self.stdout.write(
            f"\nRAG cognitive-boosters ablation — "
            f"{total - skipped}/{total} queries (skipped {skipped})"
        )
        self.stdout.write(f"{'metric':<20}{'OFF':>10}{'ON':>10}{'delta':>14}")
        wins = 0
        for m in METRICS:
            off = mean(agg["OFF"].get(m, []))
            on = mean(agg["ON"].get(m, []))
            delta = on - off
            if delta > 0:
                wins += 1
            self.stdout.write(f"{m:<20}{off:>10.4f}{on:>10.4f}{delta:>+14.4f}")

        if wins >= 2:
            verdict = "ON improves on a majority of metrics"
        else:
            verdict = (
                "ON does NOT beat OFF on a majority of metrics "
                "-> boosters are demotion candidates"
            )
        self.stdout.write(
            self.style.NOTICE(f"\nVerdict: {verdict} ({wins}/3 improved)")
        )
