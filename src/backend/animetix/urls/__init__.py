from django.urls import path, include, re_path
from .. import views
from ..views.spa import spa_view

urlpatterns = [
    path('', views.index, name='index'),
    path('api/v1/', include('animetix.urls.api')),
    path('games/', include('animetix.urls.games')),
    path('social/', include('animetix.urls.social')),
    path('donation/', include('animetix.urls.donation')),
    path('audio/', include('animetix.urls.audio')),
    path('emoji/', include('animetix.urls.emoji')),
    path('mlops/', include('animetix.urls.mlops')),
    
    path('switch_mode/<str:mode>/', views.switch_mode, name='switch_mode'),
    path('switch_language/<str:lang>/', views.switch_language, name='switch_language'),
    path('switch_lang/<str:lang>/', views.switch_language, name='switch_lang'),
    path('switch_difficulty/<str:diff>/', views.switch_difficulty, name='switch_difficulty'),
    path('custom_config/', views.custom_config_view, name='custom_config'),
    path('save_custom_config/', views.save_custom_config, name='save_custom_config'),
    
    # Règle catch-all pour React SPA
    re_path(r'^(?!api/|static/|admin/).*$', spa_view, name='spa-fallback'),
]
