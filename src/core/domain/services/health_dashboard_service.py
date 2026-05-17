from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from core.ports.donation_port import DonationPort
from core.ports.usage_port import UsagePort

class HealthDashboardService:
    def __init__(self, donation_port: DonationPort, usage_port: UsagePort):
        self.donation_port = donation_port
        self.usage_port = usage_port

    def get_health_stats(self) -> Dict[str, Any]:
        """
        Gathers stats for the transparency dashboard.
        Compiles total costs vs total donations.
        """
        # We can look at the last 30 days or total
        since_30d = datetime.now() - timedelta(days=30)
        
        total_donations = self.donation_port.get_total_donations()
        total_costs = self.usage_port.get_total_cost()
        
        recent_donations = self.donation_port.get_recent_donations(limit=5)
        
        # Monthly stats
        monthly_donations = self.donation_port.get_total_donations(since=since_30d)
        monthly_costs = self.usage_port.get_total_cost(since=since_30d)
        
        # Balance
        health_percentage = (total_donations / total_costs * 100) if total_costs > 0 else 100.0
        
        return {
            "total_donations": round(total_donations, 2),
            "total_costs": round(total_costs, 2),
            "monthly_donations": round(monthly_donations, 2),
            "monthly_costs": round(monthly_costs, 2),
            "health_percentage": min(round(health_percentage, 1), 100.0),
            "recent_donations": recent_donations,
            "is_sustainable": total_donations >= total_costs
        }
