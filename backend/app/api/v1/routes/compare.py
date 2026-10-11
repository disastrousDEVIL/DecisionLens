import asyncio

from fastapi import APIRouter, HTTPException

from app.providers.registry import get_providers
from app.schemas.decisions import CompareRequest, CompareResponse

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest) -> CompareResponse:
    providers = get_providers()
    unknown = sorted(set(request.providers) - providers.keys())
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown provider(s): {', '.join(unknown)}")

    results = await asyncio.gather(*(providers[slug].decide(request.decision) for slug in request.providers))
    return CompareResponse(results=results)

