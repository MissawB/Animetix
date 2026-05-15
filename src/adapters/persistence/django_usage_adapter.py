from typing import Optional
from core.ports.usage_port import UsagePort
from animetix.models import AITokenUsage

class DjangoUsageAdapter(UsagePort):
    def log_usage(
        self, 
        engine: str, 
        input_tokens: int, 
        output_tokens: int, 
        user_id: Optional[int] = None
    ):
        """
        Saves token usage to Django database.
        Estimates cost based on engine (Placeholders for pricing).
        """
        # Simplistic cost estimation (USD per 1M tokens)
        pricing = {
            'gpt-4o': {'in': 5.0, 'out': 15.0},
            'gpt-3.5-turbo': {'in': 0.5, 'out': 1.5},
            'claude-3-sonnet': {'in': 3.0, 'out': 15.0},
            'local-llama': {'in': 0.0, 'out': 0.0},
            'brain-api': {'in': 1.0, 'out': 2.0}, # Internal pricing
        }
        
        # Fallback pricing
        engine_price = pricing.get(engine, {'in': 1.0, 'out': 2.0})
        
        cost = (input_tokens / 1_000_000 * engine_price['in']) + \
               (output_tokens / 1_000_000 * engine_price['out'])
        
        AITokenUsage.objects.create(
            user_id=user_id,
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_estimate=cost
        )
