from django.urls import path, include, re_path
from . import views
from .views.spa import spa_view

urlpatterns = [
    path('', views.index, name='index'),
    path('api/v1/', include('animetix.urls.api')),
    path('games/', include('animetix.urls.games')),
    path('social/', include('animetix.urls.social')),
    
    # Règle catch-all pour React SPA
    re_path(r'^(?!api/|static/|admin/).*$', spa_view, name='spa-fallback'),
]
