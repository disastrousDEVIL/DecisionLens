from fastapi import APIRouter

from app.providers.registry import get_providers

router = APIRouter()


@router.get("")
async def list_providers() -> list[dict[str, object]]:
    """Return provider availability and capability snapshots without exposing secrets."""
    return [
        {
            "slug": provider.slug,
            "display_name": provider.display_name,
            "available": provider.is_available(),
            "capabilities": provider.capabilities().model_dump(),
        }
        for provider in get_providers().values()
    ]

