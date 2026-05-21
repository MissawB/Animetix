from django.urls import path
from .. import views

urlpatterns = [
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('social/dashboard/', views.social_dashboard, name='social_dashboard'),
]
