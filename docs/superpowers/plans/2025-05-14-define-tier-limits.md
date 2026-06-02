# Task 2: Define Tier Limits in PricingService Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define and implement tier-based usage limits (tokens and requests) in the `PricingService`.

**Architecture:** Extend the `PricingService` with a `TIER_LIMITS` constant mapping tier names to their respective token and request quotas, and provide a `get_limits` method to retrieve them.

**Tech Stack:** Python, Pytest

---

### Task 1: Setup tests and verify existing behavior (Optional but recommended for TDD)

**Files:**
- Create: `tests/core/test_pricing_service.py`

- [ ] **Step 1: Write a basic test for existing `calculate_cost`**

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/core/test_pricing_service.py -v`
Expected: PASS

### Task 2: Implement Tier Limits (RED)

**Files:**
- Modify: `tests/core/test_pricing_service.py`

- [ ] **Step 1: Write a failing test for `get_limits`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_pricing_service.py -v`
Expected: FAIL with "AttributeError: 'PricingService' object has no attribute 'get_limits'"

### Task 3: Implement Tier Limits (GREEN)

**Files:**
- Modify: `backend/core/domain/services/pricing_service.py`

- [ ] **Step 1: Add TIER_LIMITS and get_limits to PricingService**

```python
class PricingService:
    TIER_LIMITS = {
        'free': {'daily_tokens': 50000, 'daily_requests': 30},
        'premium': {'daily_tokens': 1000000, 'daily_requests': 500},
        'pro': {'daily_tokens': 10000000, 'daily_requests': 5000},
    }
    
    # ... existing __init__ and methods ...

    def get_limits(self, tier: str):
        return self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/core/test_pricing_service.py -v`
Expected: PASS

### Task 4: Commit

- [ ] **Step 1: Commit the changes**

Run: `git add backend/core/domain/services/pricing_service.py tests/core/test_pricing_service.py`
Run: `git commit -m "feat(pricing): add tier limits to PricingService"`
