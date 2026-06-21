from django.apps import AppConfig


class AnimetixConfig(AppConfig):
    name = "animetix"
    label = "animetix"

    def ready(self):
        # Injecte l'accès aux settings Django dans le core via ConfigPort,
        # afin que les utilitaires du domaine ne dépendent pas du framework.
        from adapters.infrastructure.django_config_adapter import (  # noqa: E402
            DjangoConfigAdapter,
        )
        from core.config import configure as configure_core  # noqa: E402

        configure_core(DjangoConfigAdapter())

        from .containers import get_container  # noqa: E402

        container = get_container()
        container.wire(
            modules=[
                "animetix.api.games.classic",
                "animetix.api.games.akinetix",
                "animetix.api.games.emoji",
                "animetix.api.games.paradox",
                "animetix.api.games.vision",
                "animetix.api.games.blindtest",
                "animetix.api.games.covertest",
                "animetix.api.games.akinetix_rl",
                "animetix.api.games.archetypist",
                "animetix.api.games.duel",
                "animetix.api.games.world_boss",
                "animetix.api.explore",
                "animetix.api.core",
                "animetix.api.social",
                "animetix.api.labs",
                "animetix.api.mlops",
                "animetix.api.graph",
                "animetix.api.companion",
                "animetix.api.dependencies",
                "animetix.api.multiverse",
                "animetix.api.observability",
                "animetix.api.forge_vn",
                "animetix.middleware",
                "animetix.views.common",
            ]
        )
        from animetix.telemetry import init_telemetry  # noqa: E402

        init_telemetry("animetix-web")
        import animetix.signals  # noqa  # noqa: E402
