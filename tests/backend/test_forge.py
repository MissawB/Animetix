import pytest
from django.contrib.auth.models import User
from animetix.models import CreativeFusion

@pytest.mark.django_db
def test_creative_fusion_model_creation():
    user = User.objects.create_user(username="forger", password="pwd")
    parent = CreativeFusion.objects.create(
        title_a="Naruto", title_b="Cyberpunk", media_type_a="Anime", media_type_b="Anime",
        scenario_text="Test", creator=user
    )
    remix = CreativeFusion.objects.create(
        title_a="Naruto", title_b="Cyberpunk", media_type_a="Anime", media_type_b="Anime",
        scenario_text="Test Remix", creator=user, parent=parent, chaos_level=80
    )
    assert remix.parent == parent
    assert remix.chaos_level == 80
