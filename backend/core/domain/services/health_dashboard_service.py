import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict

from core.ports.generic_cache_port import CachePort, InMemoryCache
from core.ports.usage_port import UsagePort

from .sota_benchmark_service import SOTABenchmarkService

logger = logging.getLogger("animetix." + __name__)


class HealthDashboardService:
    def __init__(
        self,
        usage_port: UsagePort,
        sota_service: SOTABenchmarkService = None,
        inference_engine=None,
        graph_port=None,
        cache_port: CachePort = None,
    ):
        self.usage_port = usage_port
        self.sota_service = sota_service or SOTABenchmarkService()
        self.inference_engine = inference_engine
        self.graph_port = graph_port
        self.cache = cache_port or InMemoryCache()

    def get_health_stats(self) -> Dict[str, Any]:
        """
        Gathers stats for the transparency dashboard.
        """
        since_30d = datetime.now() - timedelta(days=30)

        total_costs = self.usage_port.get_total_cost()
        monthly_costs = self.usage_port.get_total_cost(since=since_30d)

        return {
            "total_costs": round(total_costs, 2),
            "monthly_costs": round(monthly_costs, 2),
            "health_percentage": 100.0,
            "is_sustainable": False,
        }

    def get_global_health(self) -> Dict[str, Any]:
        """
        Provides advanced AI health metrics (Latency, Fidelity, RAG status).
        """
        basic_stats = self.get_health_stats()

        # simulated SOTA metrics for the transparency dashboard
        basic_stats.update(
            {
                "rag_fidelity": 0.94,
                "average_latency": 1.42,  # seconds
                "model_uptime": 99.98,
                "ethics_score": 98.5,
                "api_costs": basic_stats["total_costs"] * 0.7,
                "server_costs": basic_stats["total_costs"] * 0.3,
                "sota_benchmarks": self.sota_service.get_all_benchmarks(),
            }
        )

        return basic_stats

    def get_cluster_health(self) -> Dict[str, Any]:
        """
        Provides real-time health status for all cluster components:
        - NVIDIA H100 GPU instances (simulated metrics)
        - Ollama / Unified Inference Engine
        - Neo4j Knowledge Graph
        """
        nodes = []

        # --- NVIDIA H100 GPU Cluster (simulated) ---
        nodes.append(self._check_gpu_cluster())

        # --- Ollama / Inference Engine ---
        nodes.append(self._check_inference_engine())

        # --- Neo4j Knowledge Graph ---
        nodes.append(self._check_graph_database())

        # --- Self-Hosted AI Image Worker ---
        nodes.append(self._check_self_hosted_image_worker())

        online_count = sum(1 for n in nodes if n["status"] == "online")
        total_count = len(nodes)
        global_status = (
            "healthy"
            if online_count == total_count
            else ("degraded" if online_count > 0 else "critical")
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "global_status": global_status,
            "online_count": online_count,
            "total_count": total_count,
            "health_percentage": (
                round((online_count / total_count) * 100, 1) if total_count else 0
            ),
            "nodes": nodes,
        }

    def _check_gpu_cluster(self) -> Dict[str, Any]:
        """Simulated NVIDIA H100 GPU cluster health check."""
        # In production, this would query nvidia-smi or DCGM exporter
        import random

        gpu_count = 8
        gpus = []
        for i in range(gpu_count):
            temp = random.randint(38, 72)
            util = random.randint(15, 98)
            mem_used = round(random.uniform(8.0, 72.0), 1)
            gpus.append(
                {
                    "id": i,
                    "name": f"H100-SXM-{i}",
                    "temperature_c": temp,
                    "utilization_pct": util,
                    "memory_used_gb": mem_used,
                    "memory_total_gb": 80.0,
                    "status": "online" if temp < 85 else "throttled",
                }
            )

        avg_temp = round(sum(g["temperature_c"] for g in gpus) / len(gpus), 1)
        avg_util = round(sum(g["utilization_pct"] for g in gpus) / len(gpus), 1)

        return {
            "id": "nvidia-h100-cluster",
            "name": "NVIDIA H100 Cluster",
            "type": "gpu",
            "status": "online",
            "latency_ms": None,
            "details": {
                "gpu_count": gpu_count,
                "avg_temperature_c": avg_temp,
                "avg_utilization_pct": avg_util,
                "total_vram_gb": gpu_count * 80.0,
                "driver_version": "550.54.15",
                "cuda_version": "12.4",
            },
            "gpus": gpus,
        }

    def _check_inference_engine(self) -> Dict[str, Any]:
        """Check Ollama / Unified Inference health via adapter."""
        start = time.time()
        try:
            if self.inference_engine and hasattr(self.inference_engine, "health_check"):
                result = self.inference_engine.health_check()
                latency = round((time.time() - start) * 1000, 1)
                models = result.get("models", [])
                model_names = (
                    [m.get("name", m.get("model", "unknown")) for m in models[:10]]
                    if isinstance(models, list)
                    else []
                )

                return {
                    "id": "ollama-inference",
                    "name": "Ollama Inference Engine",
                    "type": "inference",
                    "status": result.get("status", "offline"),
                    "latency_ms": latency,
                    "details": {
                        "engine": result.get("engine", "unknown"),
                        "loaded_models": model_names,
                        "model_count": len(model_names),
                        "api_base": getattr(self.inference_engine, "api_base", "N/A"),
                    },
                }
            else:
                return {
                    "id": "ollama-inference",
                    "name": "Ollama Inference Engine",
                    "type": "inference",
                    "status": "unconfigured",
                    "latency_ms": None,
                    "details": {
                        "engine": "N/A",
                        "error": "No inference engine injected",
                    },
                }
        except Exception as e:
            latency = round((time.time() - start) * 1000, 1)
            logger.warning(f"Inference health check failed: {e}")
            return {
                "id": "ollama-inference",
                "name": "Ollama Inference Engine",
                "type": "inference",
                "status": "offline",
                "latency_ms": latency,
                "details": {"engine": "Unified", "error": str(e)},
            }

    def _check_graph_database(self) -> Dict[str, Any]:
        """Check Neo4j Knowledge Graph health via adapter."""
        start = time.time()
        try:
            if self.graph_port and hasattr(self.graph_port, "check_health"):
                is_healthy = self.graph_port.check_health()
                latency = round((time.time() - start) * 1000, 1)

                # Try to get node/relationship counts for dashboard
                node_count = 0
                rel_count = 0
                try:
                    if hasattr(self.graph_port, "execute_read"):
                        counts = self.graph_port.execute_read(
                            "MATCH (n) RETURN count(n) as cnt"
                        )
                        if counts:
                            node_count = counts[0].get("cnt", 0)
                        rels = self.graph_port.execute_read(
                            "MATCH ()-[r]->() RETURN count(r) as cnt"
                        )
                        if rels:
                            rel_count = rels[0].get("cnt", 0)
                except Exception as e:
                    logger.debug(f"Neo4j relationship count unavailable: {e}")

                return {
                    "id": "neo4j-knowledge-graph",
                    "name": "Neo4j Knowledge Graph",
                    "type": "graph_db",
                    "status": "online" if is_healthy else "offline",
                    "latency_ms": latency,
                    "details": {
                        "node_count": node_count,
                        "relationship_count": rel_count,
                        "database": "neo4j",
                        "bolt_uri": "bolt://localhost:7687",
                    },
                }
            else:
                return {
                    "id": "neo4j-knowledge-graph",
                    "name": "Neo4j Knowledge Graph",
                    "type": "graph_db",
                    "status": "unconfigured",
                    "latency_ms": None,
                    "details": {"error": "No graph port injected"},
                }
        except Exception as e:
            latency = round((time.time() - start) * 1000, 1)
            logger.warning(f"Neo4j health check failed: {e}")
            return {
                "id": "neo4j-knowledge-graph",
                "name": "Neo4j Knowledge Graph",
                "type": "graph_db",
                "status": "offline",
                "latency_ms": latency,
                "details": {"error": str(e)},
            }

    def _check_self_hosted_image_worker(self) -> Dict[str, Any]:
        """Check status and queue length of the local self-hosted image worker."""
        start = time.time()

        worker_status = self.cache.get("self_hosted_image_worker:status", "idle")
        queue_length = self.cache.get("self_hosted_image_worker:queue_length", 0)
        active_task = self.cache.get("self_hosted_image_worker:active_task", None)
        budget_exceeded = self.cache.get("paid_api_budget_exceeded", False)

        fallback_mode = (
            "active"
            if budget_exceeded or self.cache.get("paid_api_failover_active", False)
            else "nominal"
        )
        latency = round((time.time() - start) * 1000, 1)

        return {
            "id": "self-hosted-image-worker",
            "name": "Self-Hosted Image Worker",
            "type": "worker",
            "status": "online",
            "latency_ms": latency,
            "details": {
                "worker_status": worker_status,
                "queue_length": max(0, queue_length),
                "active_task": active_task,
                "fallback_mode": fallback_mode,
                "model_id": "black-forest-labs/FLUX.1-schnell",
            },
        }
