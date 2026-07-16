import pytest
from animetix.models import WalletTransaction
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status


@pytest.fixture
def test_user(db):
    user = User.objects.create_user(username="testuser", password="password")
    return user


@pytest.mark.django_db
class TestWalletAPI:
    def test_balance_pagination(self, api_client, test_user):
        # Create transactions
        for i in range(15):
            WalletTransaction.objects.create(
                user=test_user,
                amount=20,
                transaction_type="ad_passive",
                description=f"Passive mine {i}",
            )
        for i in range(5):
            WalletTransaction.objects.create(
                user=test_user,
                amount=-50,
                transaction_type="ai_usage",
                description=f"AI use {i}",
            )

        api_client.force_authenticate(user=test_user)
        url = reverse("api_wallet_balance")
        response = api_client.get(url, {"page": 1, "page_size": 10})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["history"]) == 10
        assert response.data["pagination"]["total_count"] == 20
        assert response.data["pagination"]["total_pages"] == 2
        assert response.data["pagination"]["has_next"] is True
        assert response.data["pagination"]["has_prev"] is False

    def test_balance_filtering(self, api_client, test_user):
        # Create transactions
        for i in range(15):
            WalletTransaction.objects.create(
                user=test_user,
                amount=20,
                transaction_type="ad_passive",
                description=f"Passive mine {i}",
            )
        for i in range(5):
            WalletTransaction.objects.create(
                user=test_user,
                amount=-50,
                transaction_type="ai_usage",
                description=f"AI use {i}",
            )

        api_client.force_authenticate(user=test_user)
        url = reverse("api_wallet_balance")

        # Filter by direction: debit
        response = api_client.get(url, {"direction": "debit", "page_size": 10})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["history"]) == 5
        assert all(t["amount"] < 0 for t in response.data["history"])

        # Filter by type: ad_passive
        response = api_client.get(url, {"type": "ad_passive", "page_size": 20})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["pagination"]["total_count"] == 15
        assert all(t["type"] == "ad_passive" for t in response.data["history"])

    def test_watch_ad_credits_margin_safe_reward(self, api_client, test_user):
        from core.domain.services.berrix_economy import ad_reward_bx

        api_client.force_authenticate(user=test_user)
        start = test_user.profile.wallet_balance
        resp = api_client.post(reverse("api_wallet_watch_ad"))
        assert resp.status_code == 200
        test_user.profile.refresh_from_db()
        assert resp.data["earned"] == ad_reward_bx()  # 41 at defaults, not 250
        assert test_user.profile.wallet_balance == start + ad_reward_bx()

    def test_mine_credits_capped_loss_leader(self, api_client, test_user):
        from core.domain.services.berrix_economy import MINING_REWARD_BX

        api_client.force_authenticate(user=test_user)
        resp = api_client.post(reverse("api_wallet_mine"))
        assert resp.status_code == 200
        assert resp.data["earned"] == MINING_REWARD_BX  # 10
