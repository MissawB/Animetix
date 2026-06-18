from django.urls import include, path, re_path

from ..views.spa import spa_view

urlpatterns = [
    path("", spa_view, name="index"),
    path("mlops/", include("animetix.urls.mlops")),
    # Règle catch-all pour React SPA
    re_path(r"^(?!api/|static/|admin/).*$", spa_view, name="spa-fallback"),
]
