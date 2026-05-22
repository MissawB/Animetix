from django.urls import path
from .. import views

urlpatterns = [
    path('daily/', views.start_daily_challenge, name='daily_challenge'),
    path('ranked/start/', views.start_ranked_mode, name='start_ranked'),
    path('game/start/', views.start_game, name='start_game'),
    path('game/', views.game_view, name='game'),
    path('game/guess/', views.make_guess, name='make_guess'),
    path('akinetix/', views.akinetix_view, name='akinetix'),
    path('akinetix/guess/', views.akinetix_answer, name='akinetix_guess'),
    path('akinetix/answer/', views.akinetix_answer, name='akinetix_answer'),
    path('animinator/', views.animinator_view, name='animinator'),
    path('animinator/guess/', views.animinator_guess, name='animinator_guess'),
    path('animinator/ask/', views.animinator_guess, name='animinator_ask'),
    path('archetypist/', views.archetypist_view, name='archetypist'),
    path('blindtest/', views.blindtest_view, name='blindtest'),
    path('blindtest/guess/', views.blindtest_guess, name='blindtest_guess'),
    path('covertest/', views.covertest_view, name='covertest'),
    path('covertest/guess/', views.covertest_guess, name='covertest_guess'),
    path('vision/', views.vision_quest_view, name='vision_quest'),
    path('vision/guess/', views.vision_quest_guess, name='vision_quest_guess'),
    path('spatial/', views.spatial_view, name='spatial_lab'),
    path('manga_lab/', views.manga_lab_view, name='manga_lab'),
    path('audio_lab/', views.audio_lab_view, name='audio_lab'),
    path('boss/', views.global_boss_view, name='global_boss'),
]
