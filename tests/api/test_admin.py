from unittest.mock import MagicMock, patch

import pytest
from animetix.admin import GoldDatasetEntryAdmin
from animetix.models import AIFeedback, AIREvalResult, AISafetyEvent, GoldDatasetEntry
from django.contrib import admin
from django.test import RequestFactory


# Helper to mock request messages
class MockMessageStorage:
    def __init__(self):
        self.messages = []

    def add(self, level, message, extra_tags=""):
        self.messages.append(message)


@pytest.fixture
def admin_site():
    return admin.site


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
def test_admin_registration():
    # Verify that the models are registered in the global admin site
    assert GoldDatasetEntry in admin.site._registry
    assert AIFeedback in admin.site._registry
    assert AISafetyEvent in admin.site._registry
    assert AIREvalResult in admin.site._registry


@pytest.mark.django_db
def test_gold_dataset_entry_admin_preview_methods(admin_site):
    entry = GoldDatasetEntry.objects.create(
        instruction="Short instruction",
        context="A very long context string that exceeds eighty characters to verify that the preview truncation logic works correctly and cuts it off.",
        response="Response content",
    )

    model_admin = GoldDatasetEntryAdmin(GoldDatasetEntry, admin_site)

    # Test preview methods
    assert model_admin.instruction_preview(entry) == "Short instruction"
    assert model_admin.context_preview(entry).endswith("...")
    assert "En attente" in model_admin.validation_status_display(entry)


@pytest.mark.django_db
def test_gold_dataset_entry_admin_actions(admin_site, request_factory):
    entry1 = GoldDatasetEntry.objects.create(
        instruction="I1", context="C1", response="R1", is_validated=False
    )
    entry2 = GoldDatasetEntry.objects.create(
        instruction="I2", context="C2", response="R2", is_validated=False
    )

    model_admin = GoldDatasetEntryAdmin(GoldDatasetEntry, admin_site)

    # Mock message storage on request
    req = request_factory.post("/admin/animetix/golddatasetentry/")
    setattr(req, "_messages", MockMessageStorage())

    # Run validate action
    queryset = GoldDatasetEntry.objects.filter(id__in=[entry1.id, entry2.id])
    model_admin.validate_selected(req, queryset)

    entry1.refresh_from_db()
    entry2.refresh_from_db()
    assert entry1.is_validated is True
    assert entry2.is_validated is True

    # Run invalidate action
    model_admin.invalidate_selected(req, queryset)
    entry1.refresh_from_db()
    entry2.refresh_from_db()
    assert entry1.is_validated is False
    assert entry2.is_validated is False


@pytest.mark.django_db
@patch("animetix.admin.get_container")
def test_gold_dataset_entry_admin_promote_selected(
    mock_get_container, admin_site, request_factory
):
    entry = GoldDatasetEntry.objects.create(
        instruction="I", context="C", response="R", is_validated=True
    )

    # Mock promotion service
    mock_promotion_service = MagicMock()
    mock_promotion_service.promote_validated_entries.return_value = {
        "promoted": 1,
        "details": {"QA": 1},
    }

    mock_container = MagicMock()
    mock_container.synthetic_promotion_service.return_value = mock_promotion_service
    mock_get_container.return_value = mock_container

    model_admin = GoldDatasetEntryAdmin(GoldDatasetEntry, admin_site)
    req = request_factory.post("/admin/animetix/golddatasetentry/")
    setattr(req, "_messages", MockMessageStorage())

    queryset = GoldDatasetEntry.objects.filter(id=entry.id)
    model_admin.promote_selected_entries(req, queryset)

    mock_promotion_service.promote_validated_entries.assert_called_once()


@pytest.mark.django_db
@patch("animetix.admin.get_container")
def test_gold_dataset_entry_admin_promote_view(
    mock_get_container, admin_site, request_factory
):
    mock_promotion_service = MagicMock()
    mock_promotion_service.promote_validated_entries.return_value = {
        "promoted": 2,
        "details": {"QA": 2},
    }

    mock_container = MagicMock()
    mock_container.synthetic_promotion_service.return_value = mock_promotion_service
    mock_get_container.return_value = mock_container

    model_admin = GoldDatasetEntryAdmin(GoldDatasetEntry, admin_site)
    req = request_factory.get("/admin/animetix/golddatasetentry/promote/")
    setattr(req, "_messages", MockMessageStorage())

    response = model_admin.promote_validated_view(req)

    assert response.status_code == 302
    assert response.url == "../"
    mock_promotion_service.promote_validated_entries.assert_called_once()


@pytest.mark.django_db
def test_changelist_view_adds_stats(admin_site, request_factory):
    GoldDatasetEntry.objects.create(
        instruction="I1",
        context="C1",
        response="R1",
        entry_type="QA",
        is_validated=False,
    )
    GoldDatasetEntry.objects.create(
        instruction="I2",
        context="C2",
        response="R2",
        entry_type="MULTIVERSE",
        is_validated=False,
    )
    GoldDatasetEntry.objects.create(
        instruction="I3",
        context="C3",
        response="R3",
        entry_type="QA",
        is_validated=True,
    )

    model_admin = GoldDatasetEntryAdmin(GoldDatasetEntry, admin_site)
    req = request_factory.get("/admin/animetix/golddatasetentry/")
    req.user = MagicMock()
    req.user.is_active = True
    req.user.is_staff = True
    req.user.has_perm = MagicMock(return_value=True)

    # We run changelist_view. We mock template response render or just inspect extra_context in the call.
    with patch(
        "django.contrib.admin.ModelAdmin.changelist_view"
    ) as mock_super_changelist:
        model_admin.changelist_view(req)
        mock_super_changelist.assert_called_once()
        args, kwargs = mock_super_changelist.call_args
        stats = kwargs.get("extra_context", {}).get("stats")
        assert stats is not None
        assert stats["pending_qa"] == 1
        assert stats["pending_multiverse"] == 1
        assert stats["total_validated"] == 1
