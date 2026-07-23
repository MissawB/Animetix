from .domains.ai_ml_urls import urlpatterns as ai_ml_urlpatterns
from .domains.billing_urls import urlpatterns as billing_urlpatterns
from .domains.games_urls import urlpatterns as games_urlpatterns
from .domains.manga_urls import urlpatterns as manga_urlpatterns
from .domains.social_urls import urlpatterns as social_urlpatterns

urlpatterns = (
    billing_urlpatterns
    + manga_urlpatterns
    + social_urlpatterns
    + games_urlpatterns
    + ai_ml_urlpatterns
)
