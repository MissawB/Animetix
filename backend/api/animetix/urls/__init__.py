from django.urls import path, include, re_path
from ..views.spa import spa_view

urlpatterns = [
    path('', spa_view, name='index'),
    path('api/v1/', include('animetix.urls.api')),
    path('mlops/', include('animetix.urls.mlops')),
    
    # Règle catch-all pour React SPA
    re_path(r'^(?!api/|static/|admin/).*$', spa_view, name='spa-fallback'),
]

