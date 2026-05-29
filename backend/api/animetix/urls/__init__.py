from django.urls import path, include, re_path
from ..views.spa import spa_view

urlpatterns = [
    path('', spa_view, name='index'),
    path('api/v1/', include('animetix.urls.api')),
    path('donation/', include('animetix.urls.donation')),
    path('mlops/', include('animetix.urls.mlops')),
    
    # Règle catch-all pour React SPA
    re_path(r'^(?!api/|static/|admin/).*$', spa_view, name='spa-fallback'),
]

