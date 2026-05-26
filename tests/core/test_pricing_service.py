import pytest
from core.domain.services.pricing_service import PricingService

def test_calculate_cost_llm():
    service = PricingService()
    # GPT-4o: input 5.0, output 15.0 per 1M tokens
    # 1M input + 1M output = 20.0 USD
    cost = service.calculate_cost("gpt-4o", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == 20.0

def test_calculate_cost_unit():
    service = PricingService()
    # SDXL-Turbo: 0.01 per unit
    cost = service.calculate_cost("stabilityai/sdxl-turbo", units=10)
    assert cost == 0.1

def test_get_limits_free():
    service = PricingService()
    limits = service.get_limits("free")
    assert limits == {'daily_tokens': 50000, 'daily_requests': 30}

def test_get_limits_premium():
    service = PricingService()
    limits = service.get_limits("premium")
    assert limits == {'daily_tokens': 1000000, 'daily_requests': 500}

def test_get_limits_default_to_free():
    service = PricingService()
    limits = service.get_limits("unknown")
    assert limits == {'daily_tokens': 50000, 'daily_requests': 30}
