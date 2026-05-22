from django.urls import path
from .. import views

urlpatterns = [
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('social/dashboard/', views.social_dashboard, name='social_dashboard'),
    path('toggle_collection/<int:fusion_id>/', views.toggle_collection, name='toggle_collection'),
    path('my_collection/', views.my_collection, name='my_collection'),
    path('toggle_follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('notifications/', views.notifications_list_view, name='notifications'),
]
