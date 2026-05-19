from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('switch_mode/<str:mode>/', views.switch_mode, name='switch_mode'),
    path('switch_lang/<str:lang>/', views.switch_language, name='switch_lang'),
    path('switch_diff/<str:diff>/', views.switch_difficulty, name='switch_diff'),
    
    path('daily/', views.start_daily_challenge, name='daily_challenge'),
    path('ranked/start/', views.start_ranked_mode, name='start_ranked'),
    path('ranked/next/', views.ranked_next_level, name='ranked_next'),
    
    path('custom/config/', views.custom_config_view, name='custom_config'),
    path('custom/save/', views.save_custom_config, name='save_custom_config'),
    
    path('game/start/', views.start_game, name='start_game'),
    path('game/', views.game_view, name='game'),
    path('game/guess/', views.make_guess, name='make_guess'),
    path('game/reveal/<str:hint_type>/', views.reveal_hint, name='reveal_hint'),
    path('game/abandon/', views.abandon_game, name='abandon_game'),
    
    path('vision/', views.vision_quest_view, name='vision_quest'),
    path('vision/guess/', views.vision_quest_guess, name='vision_quest_guess'),
    
    path('emoji/', views.emoji_decode_view, name='emoji_decode'),
    path('emoji/guess/', views.emoji_decode_guess, name='emoji_guess'),
    path('emoji/stream/', views.emoji_decode_stream, name='emoji_stream'),

    path('animinator/', views.animinator_view, name='animinator'),
    path('animinator/ask/', views.animinator_ask, name='animinator_ask'),
    path('animinator/stream/', views.animinator_stream, name='animinator_stream'),
    path('animinator/guess/', views.animinator_guess, name='animinator_guess'),
    
    path('akinetix/', views.akinetix_view, name='akinetix'),
    path('akinetix/answer/', views.akinetix_answer, name='akinetix_answer'),
    path('akinetix/confirm/', views.akinetix_confirm, name='akinetix_confirm'),
    
    path('paradox/', views.paradox_view, name='paradox'),
    path('paradox/guess/', views.paradox_guess, name='intruder_guess'),
    path('paradox/stream/', views.paradox_stream, name='paradox_stream'),
    
    path('blindtest/', views.blindtest_view, name='blindtest'),
    path('blindtest/guess/', views.blindtest_guess, name='blindtest_guess'),
    
    path('covertest/', views.covertest_view, name='covertest'),
    path('covertest/guess/', views.covertest_guess, name='covertest_guess'),
    
    path('undercover/setup/', views.undercover_party_setup, name='undercover_party_setup'),
    path('undercover/play/', views.undercover_party_play, name='undercover_party_play'),
    path('undercover/join/', views.undercover_online_join, name='undercover_online_join'),
    
    path('codemanga/', views.codemanga_setup, name='codemanga'),
    path('codemanga/room/<str:room_code>/', views.codemanga_room, name='codemanga_room'),
    path('codemanga/game/<str:room_code>/', views.codemanga_game, name='codemanga_game'),
    
    path('archetypist/', views.archetypist_view, name='archetypist'),
    path('fusion/like/<int:fusion_id>/', views.like_fusion, name='like_fusion'),
    path('task/<str:task_id>/', views.get_task_status, name='task_status'),

    path('sync_offline/', views.sync_offline_data, name='sync_offline'),
    
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('social/follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('social/toggle_follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('social/dashboard/', views.social_dashboard, name='social_dashboard'),
    path('social/collection/', views.my_collection, name='my_collection'),
    path('social/collection/toggle/<int:fusion_id>/', views.toggle_collection, name='toggle_collection'),
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/mark_read/', views.mark_notifications_read, name='mark_notifications_read'),


    
    path('duel/create/', views.create_duel, name='create_duel'),
    path('duel/join/', views.join_duel, name='join_duel'),
    path('duel/room/<str:room_code>/', views.duel_room_view, name='duel_room'),
    path('duel/finish/<str:room_code>/', views.finish_duel, name='finish_duel'),
    
    path('boss/', views.global_boss_view, name='global_boss'),
    path('boss/guess/', views.global_boss_guess, name='global_boss_guess'),
    
    path('health/', views.health_check_view, name='health_check'),
    path('admin/ai_eval/', views.ai_evaluation_dashboard, name='ai_eval_dashboard'),
    path('admin/gold/', views.gold_curation_view, name='gold_curation'),
    path('admin/gold/validate/<int:entry_id>/', views.validate_gold_entry, name='validate_gold'),
    path('admin/gold/reject/<int:entry_id>/', views.reject_gold_entry, name='reject_gold'),
    
    path('latent_space/', views.latent_space_view, name='latent_space'),
    path('spatial/', views.spatial_view, name='spatial_lab'),
    path('spatial/depth/', views.generate_depth, name='generate_depth'),
    path('manga_lab/', views.manga_lab_view, name='manga_lab'),
    path('manga_lab/clean/', views.process_manga_bubbles, name='process_manga_bubbles'),
    path('manga_lab/translate/', views.translate_manga_bubbles, name='translate_manga_bubbles'),
    path('transparency/', views.transparency_dashboard, name='transparency'),
    path('api/webhooks/donation/', views.donation_webhook, name='donation_webhook'),
    path('feedback/ai/', views.submit_ai_feedback, name='submit_ai_feedback'),
    path('rag/stream/', views.agentic_rag_stream, name='agentic_rag_stream'),
]
