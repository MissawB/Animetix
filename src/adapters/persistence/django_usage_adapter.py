from typing import Optional
from datetime import datetime
from django.db.models import Sum
from core.ports.usage_port import UsagePort
from core.domain.services.pricing_service import PricingService
from animetix.models import AITokenUsage

class DjangoUsageAdapter(UsagePort):
    def __init__(self, pricing_service: Optional[PricingService] = None):
        self.pricing_service = pricing_service or PricingService()

    def log_usage(
        self, 
        engine: str, 
        input_tokens: int = 0, 
        output_tokens: int = 0, 
        units: int = 0,
        user_id: Optional[int] = None
    ):
        """
        Saves usage to Django database.
        Uses PricingService for accurate cost calculation.
        """
        cost = self.pricing_service.calculate_cost(
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            units=units
        )
        
        AITokenUsage.objects.create(
            user_id=user_id,
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens + units,
            cost_estimate=cost
        )

    def get_total_cost(self, since: Optional[datetime] = None) -> float:
        query = AITokenUsage.objects.all()
        if since:
            query = query.filter(created_at__gte=since)
        return query.aggregate(total=Sum('cost_estimate'))['total'] or 0.0
