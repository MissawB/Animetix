import pytest
from unittest.mock import MagicMock, patch
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from animetix.models import CreativeFusion


@pytest.mark.django_db
def test_django_storage_local_saving():
    # Verify that saving via default_storage works (local storage in test environment)
    file_name = "test_fusions/test_image.txt"
    content = b"fake-image-bytes"

    if default_storage.exists(file_name):
        default_storage.delete(file_name)

    saved_path = default_storage.save(file_name, ContentFile(content))
    assert default_storage.exists(saved_path)

    # Read content back
    with default_storage.open(saved_path) as f:
        read_content = f.read()
    assert read_content == content

    # Clean up
    default_storage.delete(saved_path)


@pytest.mark.django_db
@patch("animetix.api.games.archetypist.AsyncResult")
def test_archetypist_task_status_view_saves_to_storage(
    mock_async_result, client, django_user_model
):
    # Create user and authenticate
    user = django_user_model.objects.create_user(
        username="testuser", password="password"
    )
    client.force_login(user)

    # Create a creative fusion entry
    fusion = CreativeFusion.objects.create(
        title_a="Naruto",
        title_b="One Piece",
        media_type_a="Anime",
        media_type_b="Anime",
        scenario_text="Génération en cours...",
        creator=user,
    )

    # Mock celery task state and result
    mock_task = MagicMock()
    mock_task.ready.return_value = True
    mock_task.state = "SUCCESS"

    fake_base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    mock_task.result = {
        "scenario": "A crossover between Naruto and Luffy.",
        "fusion_image": fake_base64_image,
    }
    mock_async_result.return_value = mock_task

    # Set the mocked task data in Django cache since the view reads from cache
    from django.core.cache import cache  # noqa: E402

    cache.set(
        "task_result:mock-task-id",
        {"state": "SUCCESS", "ready": True, "result": mock_task.result},
    )

    # Make GET request to the ArchetypistTaskStatusView using the correct prefix path /api/v1/
    response = client.get(
        f"/api/v1/archetypist/status/?task_id=mock-task-id&fusion_id={fusion.id}"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["scenario"] == "A crossover between Naruto and Luffy."
    assert "media/fusions/fusion_" in data["image_url"]

    # Verify DB state is updated
    updated_fusion = CreativeFusion.objects.get(id=fusion.id)
    assert updated_fusion.scenario_text == "A crossover between Naruto and Luffy."
    assert updated_fusion.image_url == data["image_url"]

    # Clean up created file from default_storage
    file_name = updated_fusion.image_url.split("/media/")[-1]
    if default_storage.exists(file_name):
        default_storage.delete(file_name)

    # Clear cache
    cache.delete("task_result:mock-task-id")
