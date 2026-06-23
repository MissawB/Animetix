from unittest.mock import MagicMock, patch

from django.test import RequestFactory

from backend.api.animetix.api.companion import CompanionInteractView


def test_companion_interact_view_unauthenticated():
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/companion/interact/", {"mentor_id": "sensei", "user_message": "Hello"}
    )
    view = CompanionInteractView.as_view()
    response = view(request)
    # DRF permissions usually return 403 or 401 for unauthenticated
    assert response.status_code in [401, 403]


def test_companion_interact_view_authenticated():
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/companion/interact/",
        {
            "mentor_id": "sensei",
            "user_message": "Hello",
            "context_url": "http://test.com",
        },
        content_type="application/json",
    )

    # Mock user and authentication
    user = MagicMock()
    user.id = 1
    user.tier = "free"
    user.is_authenticated = True
    request.user = user
    request.session = {}

    with (
        patch("backend.api.animetix.api.companion.get_container") as mock_get_container,
        patch("animetix.api.billing.deduct_berrix"),
    ):
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Compagnon says hello!"
        mock_container.core.companion_service.return_value = mock_service

        mock_guard = MagicMock()
        mock_guard.validate_input.return_value = {"is_safe": True}
        mock_guard.validate_output.return_value = {"is_safe": True}
        mock_container.core.guardrail_service.return_value = mock_guard

        mock_usage = MagicMock()
        mock_usage.check_quota.return_value = True
        mock_container.infrastructure.usage_port.return_value = mock_usage

        mock_get_container.return_value = mock_container

        # Bypass permissions for testing or ensure user is authenticated
        from rest_framework.test import force_authenticate  # noqa: E402

        view = CompanionInteractView.as_view(permission_classes=[])
        force_authenticate(request, user=user)
        response = view(request)

        assert response.status_code == 200
        assert response.data["response"] == "Compagnon says hello!"
        assert len(response.data["history"]) == 2
        assert response.data["history"][1]["content"] == "Compagnon says hello!"


def test_companion_evicts_and_remembers_when_over_five_turns():
    factory = RequestFactory()
    request = factory.post(
        "/api/v1/companion/interact/",
        {"mentor_id": "sensei", "user_message": "Hello", "context_url": ""},
        content_type="application/json",
    )
    user = MagicMock()
    user.id = 1
    user.tier = "free"
    user.is_authenticated = True
    request.user = user
    prior = [{"role": "user", "content": f"old{i}"} for i in range(4)]
    request.session = {"companion_history": list(prior)}

    with (
        patch("backend.api.animetix.api.companion.get_container") as mock_get_container,
        patch("animetix.api.billing.deduct_berrix"),
    ):
        mock_container = MagicMock()
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "hi back"
        mock_container.core.companion_service.return_value = mock_service
        mock_guard = MagicMock()
        mock_guard.validate_input.return_value = {"is_safe": True}
        mock_guard.validate_output.return_value = {"is_safe": True}
        mock_container.core.guardrail_service.return_value = mock_guard
        mock_container.infrastructure.usage_port.return_value = MagicMock()
        mock_get_container.return_value = mock_container

        from rest_framework.test import force_authenticate  # noqa: E402

        view = CompanionInteractView.as_view(permission_classes=[])
        force_authenticate(request, user=user)
        response = view(request)

    assert response.status_code == 200
    # the window keeps the last 5 turns
    assert len(response.data["history"]) == 5
    # the single evicted turn was handed to long-term memory
    mock_service.remember.assert_called_once()
    args = mock_service.remember.call_args.args
    assert args[0] == 1 and args[1] == [prior[0]]
    # generate_response was given the user id for retrieval
    assert mock_service.generate_response.call_args.kwargs["user_id"] == 1
