from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('switch_mode/<str:mode>/', views.switch_mode, name='switch_mode'),
    path('switch_lang/<str:lang>/', views.switch_language, name='switch_lang'),
    path('switch_diff/<str:diff>/', views.switch_difficulty, name='switch_diff'),
    path('start_game/', views.start_game, name='start_game'),
    path('daily/', views.start_daily_challenge, name='daily_challenge'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('game/', views.game_view, name='game'),
    path('game/abandon/', views.abandon_game, name='abandon_game'),
    path('game/hint/<str:hint_type>/', views.reveal_hint, name='reveal_hint'),
    path('make_guess/', views.make_guess, name='make_guess'),
    path('archetypist/', views.archetypist_view, name='archetypist'),
    path('paradox/', views.paradox_view, name='paradox'),
    path('paradox/guess/', views.paradox_guess, name='intruder_guess'),
    path('undercover/party/setup/', views.undercover_party_setup, name='undercover_party_setup'),
    path('undercover/party/play/', views.undercover_party_play, name='undercover_party_play'),
    path('undercover/online/join/', views.undercover_online_join, name='undercover_online_join'),
    path('undercover/online/room/<str:room_code>/', views.undercover_online_room, name='undercover_online_room'),
    path('codemanga/', views.codemanga_setup, name='codemanga'),
    path('codemanga/room/<str:room_code>/', views.codemanga_room, name='codemanga_room'),
    path('codemanga/game/<str:room_code>/', views.codemanga_game, name='codemanga_game'),
    path('emoji/', views.emoji_decode_view, name='emoji_decode'),
    path('emoji/guess/', views.emoji_decode_guess, name='emoji_guess'),
    
    # MODE 1 : Animninator (User asks AI)
    path('animinator/', views.animinator_view, name='animinator'),
    path('animinator/ask/', views.animinator_ask, name='animinator_ask'),
    path('animinator/guess/', views.animinator_guess, name='animinator_guess'),
    
    # MODE 2 : Akinetix (AI asks User)
    path('akinetix/', views.akinetix_view, name='akinetix'),
    path('akinetix/answer/', views.akinetix_answer, name='akinetix_answer'),
    path('akinetix/confirm/', views.akinetix_confirm, name='akinetix_confirm'),
    
    # MODE RANKED
    path('ranked/start/', views.start_ranked_mode, name='start_ranked'),
    path('ranked/next/', views.ranked_next_level, name='ranked_next'),
    
    # MODE CUSTOM
    path('custom/config/', views.custom_config_view, name='custom_config'),
    path('custom/save/', views.save_custom_config, name='save_custom_config'),
    
    # FEEDBACK IA
    path('ai/feedback/', views.submit_ai_feedback, name='submit_ai_feedback'),
    
    # VISUALISATION IA (LATENT SPACE)
    path('ai/latent-space/', views.latent_space_view, name='latent_space'),
    
    # MODE MULTIMODAL (VISION QUEST)
    path('vision-quest/', views.vision_quest_view, name='vision_quest'),
    path('vision-quest/guess/', views.vision_quest_guess, name='vision_quest_guess'),

    # MODE 4 : BLIND TEST
    path('blindtest/', views.blindtest_view, name='blindtest'),
    path('blindtest/guess/', views.blindtest_guess, name='blindtest_guess'),

    # MODE 5 : COVER TEST
    path('covertest/', views.covertest_view, name='covertest'),
    path('covertest/guess/', views.covertest_guess, name='covertest_guess'),

    # ASYNC TASKS (CELERY)
    path('tasks/status/<str:task_id>/', views.get_task_status, name='task_status'),
]
