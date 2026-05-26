import pytest
from django.contrib.auth.models import User
from adapters.persistence.django_usage_adapter import DjangoUsageAdapter
from animetix.models import AITokenUsage
from django.utils import timezone

@pytest.mark.django_db
def test_check_quota_within_limits():
    user = User.objects.create_user(username="testuser_within")
    adapter = DjangoUsageAdapter()
    
    # Free tier limits: 50000 tokens, 30 requests
    # Log some usage
    adapter.log_usage(engine="gpt-3.5-turbo", input_tokens=1000, output_tokens=1000, user_id=user.id)
    
    assert adapter.check_quota(user.id, "free") is True

@pytest.mark.django_db
def test_check_quota_exceed_tokens():
    user = User.objects.create_user(username="testuser_tokens")
    adapter = DjangoUsageAdapter()
    
    # Free tier limit: 50000 tokens
    # Total tokens = 30000 + 20001 = 50001
    adapter.log_usage(engine="gpt-3.5-turbo", input_tokens=30000, output_tokens=20001, user_id=user.id)
    
    assert adapter.check_quota(user.id, "free") is False

@pytest.mark.django_db
def test_check_quota_exceed_requests():
    user = User.objects.create_user(username="testuser_requests")
    adapter = DjangoUsageAdapter()
    
    # Free tier limit: 30 requests
    for _ in range(30):
        adapter.log_usage(engine="gpt-3.5-turbo", input_tokens=1, output_tokens=1, user_id=user.id)
    
    # 30 requests is exactly the limit. The implementation says `used_requests >= limits['daily_requests']`.
    # Let's check if 30th request is allowed.
    # If used_requests is 30, it returns False.
    assert adapter.check_quota(user.id, "free") is False
    
@pytest.mark.django_db
def test_check_quota_reset_next_day():
    user = User.objects.create_user(username="testuser_reset")
    adapter = DjangoUsageAdapter()
    
    # Log usage for yesterday
    yesterday = timezone.now() - timezone.timedelta(days=1)
    usage = AITokenUsage.objects.create(
        user=user,
        engine="gpt-3.5-turbo",
        total_tokens=100000,
        cost_estimate=1.0
    )
    # Manually set created_at because auto_now_add=True makes it hard to change on create
    AITokenUsage.objects.filter(id=usage.id).update(created_at=yesterday)
    
    # Should be True for today as yesterday's usage doesn't count
    assert adapter.check_quota(user.id, "free") is True

@pytest.mark.django_db
def test_check_quota_different_tiers():
    user = User.objects.create_user(username="testuser_tiers")
    adapter = DjangoUsageAdapter()
    
    # Log 60000 tokens (Exceeds free limit 50000, but within premium 1000000)
    adapter.log_usage(engine="gpt-3.5-turbo", input_tokens=30000, output_tokens=30000, user_id=user.id)
    
    assert adapter.check_quota(user.id, "free") is False
    assert adapter.check_quota(user.id, "premium") is True
