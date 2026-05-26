import pytest
from django.contrib.auth.models import User
from animetix.models import Profile
from core.domain.entities.user import UserProfile
from adapters.persistence.django_profile_adapter import DjangoProfileAdapter

@pytest.mark.django_db
class TestProfileModel:
    def test_profile_tier_defaults_to_free(self):
        user = User.objects.create_user(username="testuser")
        # Profile is created via signal
        assert user.profile.tier == 'free'

    def test_profile_api_key_is_none_by_default(self):
        user = User.objects.create_user(username="testuser_key")
        assert user.profile.api_key is None

    def test_profile_tier_choices(self):
        user = User.objects.create_user(username="testuser_choices")
        user.profile.tier = 'premium'
        user.profile.save()
        
        # Reload from DB
        profile = Profile.objects.get(id=user.profile.id)
        assert profile.tier == 'premium'
        
        profile.tier = 'pro'
        profile.save()
        assert Profile.objects.get(id=user.profile.id).tier == 'pro'

    def test_profile_api_key_uniqueness(self):
        user1 = User.objects.create_user(username="user1")
        user1.profile.api_key = "secret_key_123"
        user1.profile.save()

        user2 = User.objects.create_user(username="user2")
        user2.profile.api_key = "secret_key_123"
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            user2.profile.save()

@pytest.mark.django_db
class TestDjangoProfileAdapter:
    def test_to_domain_mapping(self):
        user = User.objects.create_user(username="adapter_user")
        profile = user.profile
        profile.xp = 100
        profile.tier = 'premium'
        profile.api_key = "test_api_key"
        profile.save()

        domain_profile = DjangoProfileAdapter.to_domain(profile)
        
        assert isinstance(domain_profile, UserProfile)
        assert domain_profile.username == "adapter_user"
        assert domain_profile.xp == 100
        assert domain_profile.tier == 'premium'
        assert domain_profile.api_key == "test_api_key"

    def test_update_django_mapping(self):
        user = User.objects.create_user(username="update_user")
        profile = user.profile
        
        domain_profile = UserProfile(
            id=user.id,
            username="update_user",
            xp=500,
            tier='pro',
            api_key='new_key'
        )
        
        DjangoProfileAdapter.update_django(profile, domain_profile)
        
        # Reload from DB
        updated_profile = Profile.objects.get(id=profile.id)
        assert updated_profile.xp == 500
        assert updated_profile.tier == 'pro'
        assert updated_profile.api_key == 'new_key'
