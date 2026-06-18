import pytest
from adapters.persistence.django_profile_adapter import DjangoProfileAdapter
from animetix.models import Profile
from core.domain.entities.user import UserProfile
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestProfileModel:
    def test_profile_tier_defaults_to_free(self):
        user = User.objects.create_user(username="testuser")
        # Profile is created via signal
        assert user.profile.tier == "free"

    def test_profile_api_key_is_none_by_default(self):
        user = User.objects.create_user(username="testuser_key")
        assert user.profile.api_key_hash is None

    def test_profile_api_key_hashing(self):
        user = User.objects.create_user(username="testuser_hash")
        user.profile.set_api_key("my-secret-key")
        user.profile.save()

        assert user.profile.api_key_hash is not None
        assert user.profile.api_key_hash != "my-secret-key"
        assert user.profile.check_api_key("my-secret-key") is True
        assert user.profile.check_api_key("wrong-key") is False

    def test_profile_tier_choices(self):
        user = User.objects.create_user(username="testuser_choices")
        user.profile.tier = "premium"
        user.profile.save()

        # Reload from DB
        profile = Profile.objects.get(id=user.profile.id)
        assert profile.tier == "premium"

        profile.tier = "pro"
        profile.save()
        assert Profile.objects.get(id=user.profile.id).tier == "pro"

    def test_profile_api_key_uniqueness(self):
        user1 = User.objects.create_user(username="user1")
        user1.profile.api_key_hash = "same_hash_123"
        user1.profile.save()

        user2 = User.objects.create_user(username="user2")
        user2.profile.api_key_hash = "same_hash_123"

        from django.db import IntegrityError  # noqa: E402

        with pytest.raises(IntegrityError):
            user2.profile.save()


@pytest.mark.django_db
class TestDjangoProfileAdapter:
    def test_to_domain_mapping(self):
        user = User.objects.create_user(username="adapter_user")
        profile = user.profile
        profile.xp = 100
        profile.tier = "premium"
        profile.set_api_key("test_api_key")
        profile.save()

        domain_profile = DjangoProfileAdapter.to_domain(profile)

        assert isinstance(domain_profile, UserProfile)
        assert domain_profile.username == "adapter_user"
        assert domain_profile.xp == 100
        assert domain_profile.tier == "premium"
        # In domain, api_key now holds the hash when coming from DB
        assert domain_profile.api_key == profile.api_key_hash

    def test_update_django_mapping(self):
        user = User.objects.create_user(username="update_user")
        profile = user.profile

        domain_profile = UserProfile(
            id=user.id, username="update_user", xp=500, tier="pro", api_key="new_key"
        )

        DjangoProfileAdapter.update_django(profile, domain_profile)

        # Reload from DB
        updated_profile = Profile.objects.get(id=profile.id)
        assert updated_profile.xp == 500
        assert updated_profile.tier == "pro"
        assert updated_profile.check_api_key("new_key") is True


@pytest.mark.django_db
def test_user_recommendation_creation():
    from animetix.models import MediaItem, UserRecommendation  # noqa: E402

    user = User.objects.create_user(username="rec_tester", password="pwd")
    media = MediaItem.objects.create(
        external_id="123", media_type="Anime", title="Death Note"
    )

    rec = UserRecommendation.objects.create(
        user=user, media_item=media, score=4.85, rank=1
    )

    assert rec.id is not None
    assert rec.score == 4.85
    assert rec.rank == 1
    assert str(rec) == "Rec for rec_tester: Death Note (Rank 1)"
