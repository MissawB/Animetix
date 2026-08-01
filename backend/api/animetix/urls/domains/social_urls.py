from django.urls import path

from ... import api_views

urlpatterns = [
    path(
        "clubs/",
        api_views.ClubViewSet.as_view({"get": "list", "post": "create"}),
        name="api-clubs",
    ),
    path(
        "clubs/<int:pk>/",
        api_views.ClubViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="api-club-detail",
    ),
    path(
        "clubs/<int:pk>/join/",
        api_views.ClubViewSet.as_view({"post": "join"}),
        name="api-club-join",
    ),
    path(
        "clubs/<int:pk>/leave/",
        api_views.ClubViewSet.as_view({"post": "leave"}),
        name="api-club-leave",
    ),
    path(
        "club-events/",
        api_views.ClubEventViewSet.as_view({"get": "list", "post": "create"}),
        name="api-club-events",
    ),
    path(
        "club-events/<int:pk>/",
        api_views.ClubEventViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="api-club-event-detail",
    ),
    path(
        "profile/trackers/",
        api_views.TrackerConnectionListView.as_view(),
        name="api_tracker_connections",
    ),
    path(
        "profile/trackers/link/",
        api_views.TrackerConnectionLinkView.as_view(),
        name="api_tracker_link",
    ),
    path(
        "profile/trackers/unlink/",
        api_views.TrackerConnectionUnlinkView.as_view(),
        name="api_tracker_unlink",
    ),
    path(
        "profile/trackers/links/",
        api_views.TrackerLinkListView.as_view(),
        name="api_tracker_links",
    ),
    path("config/", api_views.ConfigView.as_view(), name="api_config"),
    path("auth/login/", api_views.LoginView.as_view(), name="api_auth_login"),
    path("auth/logout/", api_views.LogoutView.as_view(), name="api_auth_logout"),
    path("auth/register/", api_views.RegisterView.as_view(), name="api_auth_register"),
    path("auth/me/", api_views.CurrentUserView.as_view(), name="api_auth_me"),
    path("leaderboard/", api_views.LeaderboardView.as_view(), name="api_leaderboard"),
    path(
        "profile/<str:username>/",
        api_views.ProfileDetailView.as_view(),
        name="api_profile_detail",
    ),
    path("social/search/", api_views.UserSearchView.as_view(), name="api_user_search"),
    path(
        "social/collection/",
        api_views.MyCollectionView.as_view(),
        name="api_collection",
    ),
    path(
        "social/notifications/",
        api_views.NotificationListView.as_view(),
        name="api_notifications",
    ),
    path(
        "social/gameplay-history/",
        api_views.GameplaySessionListView.as_view(),
        name="api_gameplay_history",
    ),
    path(
        "social/dashboard/",
        api_views.SocialViewSet.as_view({"get": "dashboard"}),
        name="api_social_dashboard",
    ),
    path(
        "social/toggle_follow/<int:pk>/",
        api_views.SocialViewSet.as_view({"post": "toggle_follow"}),
        name="api_social_toggle_follow",
    ),
    path(
        "sync/offline/",
        api_views.sync_offline_data,
        name="sync_offline_data",
    ),
    path(
        "custom-config/",
        api_views.CustomConfigDataView.as_view(),
        name="api_custom_config",
    ),
    path(
        "admin/users/",
        api_views.UserManagementViewSet.as_view({"get": "list"}),
        name="api_admin_users",
    ),
    path(
        "admin/users/<int:pk>/toggle-staff/",
        api_views.UserManagementViewSet.as_view({"post": "toggle_staff"}),
        name="api_admin_toggle_staff",
    ),
    path(
        "admin/users/<int:pk>/toggle-active/",
        api_views.UserManagementViewSet.as_view({"post": "toggle_active"}),
        name="api_admin_toggle_active",
    ),
    path("developer/rag/", api_views.DeveloperRAGView.as_view(), name="developer_rag"),
    path(
        "developer/subscribe/",
        api_views.DeveloperSubscriptionMockView.as_view(),
        name="developer_subscribe_mock",
    ),
    path(
        "developer/api-key/",
        api_views.DeveloperApiKeyView.as_view(),
        name="developer_api_key",
    ),
]
