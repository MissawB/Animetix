import pytest
from animetix.models import CreativeFusion, MarketListing, WalletTransaction
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seller(db):
    user = User.objects.create_user(username="seller", password="password")
    user.profile.wallet_balance = 100
    user.profile.save()
    return user


@pytest.fixture
def buyer(db):
    user = User.objects.create_user(username="buyer", password="password")
    user.profile.wallet_balance = 500
    user.profile.save()
    return user


@pytest.fixture
def fusion(seller):
    # Create a creative fusion owned by the seller
    fusion = CreativeFusion.objects.create(
        title_a="Goku",
        title_b="Luffy",
        media_type_a="Anime",
        media_type_b="Anime",
        scenario_text="An epic fusion of strength and rubber.",
        creator=seller,
    )
    seller.profile.collected_fusions.add(fusion)
    return fusion


@pytest.mark.django_db
def test_create_listing_success(api_client, seller, fusion):
    api_client.force_authenticate(user=seller)
    url = reverse("api-market-listings")
    payload = {"fusion": fusion.id, "price": 150}
    response = api_client.post(url, payload, format="json")

    assert response.status_code == 201
    assert MarketListing.objects.filter(
        fusion=fusion, seller=seller, price=150, is_active=True
    ).exists()


@pytest.mark.django_db
def test_create_listing_not_owner(api_client, buyer, fusion):
    # Buyer does not own the fusion, so they shouldn't be able to list it
    api_client.force_authenticate(user=buyer)
    url = reverse("api-market-listings")
    payload = {"fusion": fusion.id, "price": 150}
    response = api_client.post(url, payload, format="json")

    assert response.status_code == 400
    assert "créateur" in str(response.data)


@pytest.mark.django_db
def test_create_listing_already_listed(api_client, seller, fusion):
    # List it once
    MarketListing.objects.create(
        fusion=fusion, seller=seller, price=150, is_active=True
    )

    api_client.force_authenticate(user=seller)
    url = reverse("api-market-listings")
    payload = {"fusion": fusion.id, "price": 200}
    response = api_client.post(url, payload, format="json")

    assert response.status_code == 400
    assert "déjà en vente" in str(response.data)


@pytest.mark.django_db
def test_buy_listing_success(api_client, buyer, seller, fusion):
    listing = MarketListing.objects.create(
        fusion=fusion, seller=seller, price=200, is_active=True
    )

    api_client.force_authenticate(user=buyer)
    url = reverse("api-market-listing-buy", kwargs={"pk": listing.id})
    response = api_client.post(url)

    assert response.status_code == 200

    # Reload from DB
    buyer.profile.refresh_from_db()
    seller.profile.refresh_from_db()
    fusion.refresh_from_db()
    listing.refresh_from_db()

    # Balance check
    assert buyer.profile.wallet_balance == 300  # 500 - 200
    assert seller.profile.wallet_balance == 300  # 100 + 200

    # Ownership check
    assert fusion.creator == buyer
    assert buyer.profile.collected_fusions.filter(id=fusion.id).exists()
    assert not seller.profile.collected_fusions.filter(id=fusion.id).exists()

    # Listing state
    assert not listing.is_active

    # Transactions
    assert WalletTransaction.objects.filter(
        user=buyer, amount=-200, transaction_type="market_purchase"
    ).exists()
    assert WalletTransaction.objects.filter(
        user=seller, amount=200, transaction_type="market_sale"
    ).exists()


@pytest.mark.django_db
def test_buy_listing_insufficient_balance(api_client, buyer, seller, fusion):
    # Item costs 600, buyer only has 500
    listing = MarketListing.objects.create(
        fusion=fusion, seller=seller, price=600, is_active=True
    )

    api_client.force_authenticate(user=buyer)
    url = reverse("api-market-listing-buy", kwargs={"pk": listing.id})
    response = api_client.post(url)

    assert response.status_code == 400
    assert "insuffisant" in response.data["error"]


@pytest.mark.django_db
def test_buy_own_listing(api_client, seller, fusion):
    listing = MarketListing.objects.create(
        fusion=fusion, seller=seller, price=50, is_active=True
    )

    api_client.force_authenticate(user=seller)
    url = reverse("api-market-listing-buy", kwargs={"pk": listing.id})
    response = api_client.post(url)

    assert response.status_code == 400
    assert "propre actif" in response.data["error"]


@pytest.mark.django_db
def test_cancel_listing_success(api_client, seller, fusion):
    listing = MarketListing.objects.create(
        fusion=fusion, seller=seller, price=100, is_active=True
    )

    api_client.force_authenticate(user=seller)
    url = reverse("api-market-listing-cancel", kwargs={"pk": listing.id})
    response = api_client.post(url)

    assert response.status_code == 200
    listing.refresh_from_db()
    assert not listing.is_active


@pytest.mark.django_db
def test_cancel_listing_not_seller(api_client, buyer, seller, fusion):
    listing = MarketListing.objects.create(
        fusion=fusion, seller=seller, price=100, is_active=True
    )

    api_client.force_authenticate(user=buyer)
    url = reverse("api-market-listing-cancel", kwargs={"pk": listing.id})
    response = api_client.post(url)

    assert response.status_code == 403
