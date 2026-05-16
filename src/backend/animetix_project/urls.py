from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from rest_framework import routers
from animetix import api_views
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView

# REST Router
router = routers.DefaultRouter()
router.register(r'profiles', api_views.ProfileViewSet)
router.register(r'daily-challenges', api_views.DailyChallengeViewSet)
router.register(r'achievements', api_views.AchievementViewSet)
router.register(r'fusions', api_views.CreativeFusionViewSet)


from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', RedirectView.as_view(url='/static/animetix/img/logo/logo.png')),
    path('i18n/', include('django.conf.urls.i18n')), # Permet le switch de langue via POST
    
    # --- PROFESSIONNALISATION : API REST (Headless) ---
    path('api/', include(router.urls)),
    path('api/search/', api_views.MediaSearchView.as_view(), name='api_search'),
    path('api/session/', api_views.GameSessionView.as_view(), name='api_session'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # --- DOCUMENTATION API (Spectacular) ---
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # --- PROFESSIONNALISATION : GRAPHQL (Knowledge Graph) ---
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # --- OBSERVABILITÉ : PROMETHEUS ---
    path('metrics/', include('django_prometheus.urls')),

    # --- IMAGE PROXY (Global, no i18n) ---
    path('cdn-proxy/', api_views.image_proxy_view, name='cdn_proxy'),
]

# URLs traduites
urlpatterns += i18n_patterns(
    path('', include('animetix.urls')),
)
