"""Provider registry for enabled DecisionLens integrations."""

from app.core.config import get_settings
from app.providers.base import DecisionProvider
from app.providers.cloudflare_clef_flash import CloudflareClefFlashProvider
from app.providers.openai_decisions import OpenAIDecisionsProvider
from app.providers.typesafe_jev import TypeSafeJevProvider


def get_providers() -> dict[str, DecisionProvider]:
    """Create configured provider adapters keyed by their stable slug."""
    settings = get_settings()
    providers = [
        TypeSafeJevProvider(settings),
        CloudflareClefFlashProvider(settings),
        OpenAIDecisionsProvider(settings),
    ]
    return {provider.slug: provider for provider in providers}
