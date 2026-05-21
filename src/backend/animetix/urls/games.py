from django.urls import path
from .. import views

urlpatterns = [
    path('daily/', views.start_daily_challenge, name='daily_challenge'),
    path('ranked/start/', views.start_ranked_mode, name='start_ranked'),
    path('game/start/', views.start_game, name='start_game'),
    path('game/', views.game_view, name='game'),
    path('akinetix/', views.akinetix_view, name='akinetix'),
    path('blindtest/', views.blindtest_view, name='blindtest'),
    path('covertest/', views.covertest_view, name='covertest'),
    path('vision/', views.vision_quest_view, name='vision_quest'),
]
