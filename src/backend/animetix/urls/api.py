from django.urls import path
from .. import api_views

urlpatterns = [
    path('fusions/', api_views.CreativeFusionViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-fusions'),
    path('clubs/', api_views.ClubViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-clubs'),
    path('clubs/<int:pk>/', api_views.ClubViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='api-club-detail'),
    path('clubs/<int:pk>/join/', api_views.ClubViewSet.as_view({'post': 'join'}), name='api-club-join'),
    path('clubs/<int:pk>/leave/', api_views.ClubViewSet.as_view({'post': 'leave'}), name='api-club-leave'),
    path('achievements/', api_views.AchievementViewSet.as_view({'get': 'list'}), name='api-achievements'),
    path('search/', api_views.MediaSearchView.as_view(), name='api_search'),
    path('config/', api_views.ConfigView.as_view(), name='api_config'),
    path('auth/login/', api_views.LoginView.as_view(), name='api_auth_login'),
    path('auth/logout/', api_views.LogoutView.as_view(), name='api_auth_logout'),
    path('auth/register/', api_views.RegisterView.as_view(), name='api_auth_register'),
    path('auth/me/', api_views.CurrentUserView.as_view(), name='api_auth_me'),
    path('leaderboard/', api_views.LeaderboardView.as_view(), name='api_leaderboard'),
    path('profile/<str:username>/', api_views.ProfileDetailView.as_view(), name='api_profile_detail'),
    path('social/collection/', api_views.MyCollectionView.as_view(), name='api_collection'),
    path('social/notifications/', api_views.NotificationListView.as_view(), name='api_notifications'),
    path('latent-space/', api_views.LatentSpaceDataView.as_view(), name='api_latent_space'),
    path('daily-challenge/', api_views.DailyChallengeDataView.as_view(), name='api_daily_challenge'),
    path('custom-config/', api_views.CustomConfigDataView.as_view(), name='api_custom_config'),
    path('transparency/', api_views.TransparencyDataView.as_view(), name='api_transparency'),
    path('spatial-lab/', api_views.SpatialLabDataView.as_view(), name='api_spatial_lab'),
    path('manga-lab/', api_views.MangaLabDataView.as_view(), name='api_manga_lab'),
    path('audio-lab/', api_views.AudioLabDataView.as_view(), name='api_audio_lab'),
    path('singularity-lab/', api_views.SingularityLabDataView.as_view(), name='api_singularity_lab'),
    path('labs/video/', api_views.VideoLabDataView.as_view(), name='api_video_lab'),
    path('labs/soundscape/', api_views.SoundscapeLabDataView.as_view(), name='api_soundscape_lab'),
    path('labs/s2s/', api_views.SpeechToSpeechLabDataView.as_view(), name='api_s2s_lab'),
    path('mlops/dpo/curation/', api_views.DPOCurationView.as_view(), name='api_dpo_curation'),
    path('graph/neighbors/', api_views.GraphNeighborsView.as_view(), name='api_graph_neighbors'),
    path('companion/interact/', api_views.CompanionInteractView.as_view(), name='api_companion_interact'),
    
    # --- STREAMING IA ---
    path('stream/emoji/', api_views.EmojiStreamView.as_view(), name='api_emoji_stream'),
    path('stream/paradox/', api_views.ParadoxStreamView.as_view(), name='api_paradox_stream'),
    path('stream/agentic-rag/', api_views.AgenticRAGStreamView.as_view(), name='api_agentic_rag'),
    path('stream/animinator/', api_views.AniminatorStreamView.as_view(), name='api_animinator_stream'),
    
    # --- ARCHETYPIST (LA FORGE) ---
    path('archetypist/start/', api_views.ArchetypistStartFusionView.as_view(), name='api_archetypist_start'),
    path('archetypist/status/', api_views.ArchetypistTaskStatusView.as_view(), name='api_archetypist_status'),
    path('archetypist/vn/<int:fusion_id>/', api_views.ForgeVNView.as_view(), name='api_forge_vn'),
    
    # ... autres endpoints API
    path('game/vs_battle/run/', api_views.run_vs_battle, name='api_vs_battle_run'),
    path('game/classic/state/', api_views.ClassicGameStateView.as_view(), name='api_classic_state'),
    path('game/akinetix/state/', api_views.AkinetixGameStateView.as_view(), name='api_akinetix_state'),
    path('game/akinetix-rl/state/', api_views.AkinetixRLStateView.as_view(), name='api_akinetix_rl_state'),
    path('game/akinetix-rl/start/', api_views.AkinetixRLStartView.as_view(), name='api_akinetix_rl_start'),
    path('game/akinetix-rl/answer/', api_views.AkinetixRLAnswerView.as_view(), name='api_akinetix_rl_answer'),
    path('game/emoji/state/', api_views.EmojiGameStateView.as_view(), name='api_emoji_state'),
    path('game/paradox/state/', api_views.ParadoxGameStateView.as_view(), name='api_paradox_state'),
    path('game/vision/state/', api_views.VisionGameStateView.as_view(), name='api_vision_state'),
    path('game/blindtest/state/', api_views.BlindtestGameStateView.as_view(), name='api_blindtest_state'),
    path('game/covertest/state/', api_views.CovertestGameStateView.as_view(), name='api_covertest_state'),
]
