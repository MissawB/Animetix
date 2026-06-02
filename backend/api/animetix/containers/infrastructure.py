import os
from django.conf import settings
from dependency_injector import containers, providers

from core.domain.services.prompt_manager import PromptManager
from core.domain.services.translation_service import TranslationService
from core.domain.services.observability_service import ObservabilityService
from core.domain.services.pricing_service import PricingService
from adapters.persistence.django_usage_adapter import DjangoUsageAdapter
from adapters.persistence.web_search_adapter import UnifiedWebSearchAdapter
from adapters.infrastructure.django_notification_adapter import DjangoNotificationAdapter

class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    prompt_manager = providers.Singleton(
        PromptManager,
        prompts_dir=os.path.join(settings.PROJECT_ROOT, "src", "core", "domain", "services", "prompts")
    )

    translation_service = providers.Singleton(TranslationService)

    obs_service = providers.Singleton(
        ObservabilityService,
        project_name="animetix-production"
    )

    pricing_service = providers.Singleton(PricingService)
    
    usage_port = providers.Factory(
        DjangoUsageAdapter, 
        pricing_service=pricing_service
    )

    notification_port = providers.Singleton(
        DjangoNotificationAdapter
    )

    web_search = providers.Singleton(UnifiedWebSearchAdapter)
