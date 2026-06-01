from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from core.ports.usage_port import UsagePort
from .sota_benchmark_service import SOTABenchmarkService

class HealthDashboardService:
    def __init__(self, usage_port: UsagePort, sota_service: SOTABenchmarkService = None):
        self.usage_port = usage_port
        self.sota_service = sota_service or SOTABenchmarkService()

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
            "is_sustainable": False
        }

    def get_global_health(self) -> Dict[str, Any]:
        """
        Provides advanced AI health metrics (Latency, Fidelity, RAG status).
        """
        basic_stats = self.get_health_stats()
        
        # simulated SOTA metrics for the transparency dashboard
        basic_stats.update({
            "rag_fidelity": 0.94,
            "average_latency": 1.42, # seconds
            "model_uptime": 99.98,
            "ethics_score": 98.5,
            "api_costs": basic_stats["total_costs"] * 0.7,
            "server_costs": basic_stats["total_costs"] * 0.3,
            "sota_benchmarks": self.sota_service.get_all_benchmarks()
        })
        
        return basic_stats
