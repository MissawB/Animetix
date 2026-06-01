from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from rest_framework import routers
from animetix import api_views
from django.views.generic.base import RedirectView

# REST Router
router = routers.DefaultRouter()
router.register(r'profiles', api_views.ProfileViewSet, basename='profiles')
router.register(r'daily-challenges', api_views.DailyChallengeViewSet, basename='daily-challenges')
router.register(r'achievements', api_views.AchievementViewSet, basename='achievements')
router.register(r'fusions', api_views.CreativeFusionViewSet, basename='fusions')


from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.contrib.admin.views.decorators import staff_member_required
from django_prometheus import exports as prometheus_exports

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url='/static/animetix/img/logo/logo.png')),
    path('i18n/', include('django.conf.urls.i18n')), # Permet le switch de langue via POST
    
    # --- PROFESSIONNALISATION : API REST (Headless) ---
    path('api/v1/', include(router.urls)),
    path('api/v1/search/', api_views.MediaSearchView.as_view(), name='api_search'),
    path('api/v1/session/', api_views.GameSessionView.as_view(), name='api_session'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # --- DOCUMENTATION API (Spectacular) - Restreint au Staff ---
    path('api/schema/', staff_member_required(SpectacularAPIView.as_view()), name='schema'),
    path('api/docs/', staff_member_required(SpectacularSwaggerView.as_view(url_name='schema')), name='swagger-ui'),
    path('api/redoc/', staff_member_required(SpectacularRedocView.as_view(url_name='schema')), name='redoc'),
    
    # --- OBSERVABILITÉ : PROMETHEUS - Restreint au Staff ---
    path('metrics/', staff_member_required(prometheus_exports.ExportToDjangoView), name='prometheus-django-metrics'),

    # --- IMAGE PROXY (Global, no i18n) ---
    path('cdn-proxy/', api_views.image_proxy_view, name='cdn_proxy'),
]

# URLs traduites
urlpatterns += i18n_patterns(
    path('', include('animetix.urls')),
)
