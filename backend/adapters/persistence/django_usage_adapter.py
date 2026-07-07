from datetime import datetime
from typing import Optional

from animetix.models import AITokenUsage
from core.domain.services.pricing_service import PricingService
from core.ports.usage_port import UsagePort
from django.db.models import Count, Sum
from django.utils import timezone


class DjangoUsageAdapter(UsagePort):
    def __init__(self, pricing_service: Optional[PricingService] = None):
        self.pricing_service = pricing_service or PricingService()

    def log_usage(
        self,
        engine: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        units: int = 0,
        user_id: Optional[int] = None,
        allocated_budget: int = 0,
    ):
        """
        Saves usage to Django database.
        Uses PricingService for accurate cost calculation.
        """
        cost = self.pricing_service.calculate_cost(
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            units=units,
        )

        AITokenUsage.objects.create(
            user_id=user_id,
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens + units,
            cost_estimate=cost,
            allocated_budget=allocated_budget,
        )

    def get_total_cost(self, since: Optional[datetime] = None) -> float:
        query = AITokenUsage.objects.all()
        if since:
            query = query.filter(created_at__gte=since)
        return query.aggregate(total=Sum("cost_estimate"))["total"] or 0.0

    def check_quota(self, user_id: int, tier: str) -> bool:
        """
        Checks if a user has exceeded their daily quota based on their tier.
        """
        limits = self.pricing_service.get_limits(tier)

        today = timezone.now().date()
        stats = AITokenUsage.objects.filter(
            user_id=user_id, created_at__date=today
        ).aggregate(tokens=Sum("total_tokens"), requests=Count("id"))

        used_tokens = stats["tokens"] or 0
        used_requests = stats["requests"] or 0

        if used_tokens >= limits["daily_tokens"]:
            return False
        if used_requests >= limits["daily_requests"]:
            return False

        return True
