import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from animetix.models import DiscoveryClub, ClubMembership, Profile
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def premium_user(db):
    user = User.objects.create_user(username="premium_user", password="password")
    user.profile.tier = 'premium'
    user.profile.save()
    return user

@pytest.fixture
def free_user(db):
    user = User.objects.create_user(username="free_user", password="password")
    user.profile.tier = 'free'
    user.profile.save()
    return user

@pytest.mark.django_db
class TestClubsCRUD:
    def test_create_club_premium_success(self, api_client, premium_user):
        api_client.force_authenticate(user=premium_user)
        url = reverse('api-clubs')
        data = {
            "name": "Premium Club",
            "description": "A club for premium members",
            "theme": "Anime"
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert DiscoveryClub.objects.filter(name="Premium Club").exists()
        # Verify founder is officer
        club = DiscoveryClub.objects.get(name="Premium Club")
        assert ClubMembership.objects.filter(user=premium_user, club=club, role='Officer').exists()

    def test_create_club_free_denied(self, api_client, free_user):
        api_client.force_authenticate(user=free_user)
        url = reverse('api-clubs')
        data = {
            "name": "Free Club",
            "description": "Trying to create a club as free user",
            "theme": "Anime"
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Seuls les membres Premium" in str(response.data)

    def test_join_club_limit_free_user(self, api_client, free_user, premium_user):
        # Create 4 clubs
        clubs = []
        for i in range(4):
            club = DiscoveryClub.objects.create(
                name=f"Club {i}",
                description=f"Desc {i}",
                theme="Theme",
                creator=premium_user
            )
            clubs.append(club)

        api_client.force_authenticate(user=free_user)
        
        # Join 3 clubs
        for i in range(3):
            url = reverse('api-club-join', kwargs={'pk': clubs[i].id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        # Try to join 4th club
        url = reverse('api-club-join', kwargs={'pk': clubs[3].id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Limite de 3 clubs" in response.data['error']

    def test_leave_club(self, api_client, free_user, premium_user):
        club = DiscoveryClub.objects.create(
            name="Leave Club",
            description="Testing leave",
            theme="Theme",
            creator=premium_user
        )
        ClubMembership.objects.create(user=free_user, club=club)
        
        api_client.force_authenticate(user=free_user)
        url = reverse('api-club-leave', kwargs={'pk': club.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert not ClubMembership.objects.filter(user=free_user, club=club).exists()
