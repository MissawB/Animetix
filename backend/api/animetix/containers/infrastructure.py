import os

from dependency_injector import containers, providers
from django.conf import settings


class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    prompt_manager = providers.Singleton(
        "core.domain.services.prompt_manager.PromptManager",
        prompts_dir=os.path.join(
            settings.PROJECT_ROOT, "src", "core", "domain", "services", "prompts"
        ),
    )

    translation_service = providers.Singleton(
        "core.domain.services.translation_service.TranslationService"
    )

    obs_service = providers.Singleton(
        "core.domain.services.observability_service.ObservabilityService",
        project_name="animetix-production",
    )

    pricing_service = providers.Singleton(
        "core.domain.services.pricing_service.PricingService"
    )

    usage_port = providers.Factory(
        "adapters.persistence.django_usage_adapter.DjangoUsageAdapter",
        pricing_service=pricing_service,
    )

    user_context_port = providers.Singleton(
        "adapters.infrastructure.middleware_user_context_adapter.MiddlewareUserContextAdapter"
    )

    notification_port = providers.Singleton(
        "adapters.infrastructure.django_notification_adapter.DjangoNotificationAdapter"
    )

    web_search = providers.Singleton(
        "adapters.persistence.web_search_adapter.UnifiedWebSearchAdapter"
    )

    cache_port = providers.Singleton(
        "adapters.infrastructure.django_cache_adapter.DjangoCacheAdapter"
    )

    config_port = providers.Singleton(
        "adapters.infrastructure.django_config_adapter.DjangoConfigAdapter"
    )
