from django.urls import path
from .. import api_views

urlpatterns = [
    path('fusions/', api_views.CreativeFusionViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-fusions'),
    path('achievements/', api_views.AchievementViewSet.as_view({'get': 'list'}), name='api-achievements'),
    path('config/', api_views.ConfigView.as_view(), name='api_config'),
    
    # ... autres endpoints API
    path('game/classic/state/', api_views.ClassicGameStateView.as_view(), name='api_classic_state'),
    path('game/akinetix/state/', api_views.AkinetixGameStateView.as_view(), name='api_akinetix_state'),
    path('game/emoji/state/', api_views.EmojiGameStateView.as_view(), name='api_emoji_state'),
    path('game/paradox/state/', api_views.ParadoxGameStateView.as_view(), name='api_paradox_state'),
    path('game/vision/state/', api_views.VisionGameStateView.as_view(), name='api_vision_state'),
    path('game/blindtest/state/', api_views.BlindtestGameStateView.as_view(), name='api_blindtest_state'),
    path('game/covertest/state/', api_views.CovertestGameStateView.as_view(), name='api_covertest_state'),
]
