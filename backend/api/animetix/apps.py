from django.apps import AppConfig


class AnimetixConfig(AppConfig):
    name = 'animetix'
    label = 'animetix'

    def ready(self):
        from .containers import get_container
        container = get_container()
        container.wire(modules=[
            "animetix.api.games.classic",
            "animetix.api.games.akinetix",
            "animetix.api.games.emoji",
            "animetix.api.games.paradox",
            "animetix.api.games.vision",
            "animetix.api.games.blindtest",
            "animetix.api.games.covertest",
            "animetix.api.games.akinetix_rl",
            "animetix.api.games.archetypist",
            "animetix.api.core",
            "animetix.api.social",
            "animetix.api.labs",
            "animetix.api.mlops",
            "animetix.api.graph",
            "animetix.api.companion",
            "animetix.middleware",
            "animetix.views.common"
        ])
