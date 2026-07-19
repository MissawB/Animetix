from core.domain.services.pricing_service import PricingService
from core.utils.gemini_models import GEMINI_EMBEDDING, GEMINI_FLASH, GEMINI_LIVE


def test_calculate_cost_llm():
    service = PricingService()
    # brain-api: input 1.0, output 2.0 per 1M tokens → 1M input + 1M output = 3.0 USD
    cost = service.calculate_cost(
        "brain-api", input_tokens=1_000_000, output_tokens=1_000_000
    )
    assert cost == 3.0


def test_gemini_namespaced_engine_is_priced():
    """Live Gemini calls log namespaced engines ("google_genai:<model>[:modality]");
    these must resolve to the gemini price, not the $0 unknown-engine fallback."""
    service = PricingService()
    base = service.calculate_cost(
        "google_genai:gemini-3.5-flash",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    assert base > 0
    # a modality suffix (vision/video) resolves to the same base price
    vision = service.calculate_cost(
        "google_genai:gemini-3.5-flash:vision",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    assert vision == base


def test_dead_openai_anthropic_keys_removed():
    """The prod chain [brain_api, google_genai] never calls OpenAI/Anthropic;
    those dead registry rows are dropped."""
    service = PricingService()
    assert service.get_pricing_info("gpt-4o") is None
    assert service.get_pricing_info("gpt-3.5-turbo") is None
    assert service.get_pricing_info("claude-3-sonnet") is None


def test_all_gemini_roles_priced_nonzero():
    """All three canonical Gemini roles (flash / live / embedding) must carry a
    real input price, so none silently falls through to the $0 fallback. Uses the
    constants, so it also catches a LIVE/EMBEDDING row being dropped — cases the
    namespaced-flash test above does not exercise."""
    service = PricingService()
    for model in (GEMINI_FLASH, GEMINI_LIVE, GEMINI_EMBEDDING):
        pricing = service.get_pricing_info(model)
        assert pricing is not None, f"{model} missing from the pricing registry"
        assert pricing["input"] > 0, f"{model} has a zero input price"


def test_unknown_engine_falls_back_to_zero():
    """Genuinely unknown engines return the 0.0 fallback (billed as free)."""
    service = PricingService()
    assert (
        service.calculate_cost(
            "totally-unknown-model", input_tokens=1_000_000, output_tokens=1_000_000
        )
        == 0.0
    )


def test_calculate_cost_unit():
    service = PricingService()
    # FLUX.1-schnell: 0.03 per unit
    cost = service.calculate_cost("black-forest-labs/FLUX.1-schnell", units=10)
    assert cost == 0.3


def test_get_limits_free():
    service = PricingService()
    limits = service.get_limits("free")
    assert limits == {"daily_tokens": 50000, "daily_requests": 30}


def test_get_limits_premium():
    service = PricingService()
    limits = service.get_limits("premium")
    assert limits == {"daily_tokens": 1000000, "daily_requests": 500}


def test_get_limits_default_to_free():
    service = PricingService()
    limits = service.get_limits("unknown")
    assert limits == {"daily_tokens": 50000, "daily_requests": 30}
