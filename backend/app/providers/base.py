from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.schemas.decisions import NormalizedDecisionRequest, ProviderResult


class ProviderCapabilities(BaseModel):
    supports_binary: bool = True
    supports_choice: bool = True
    supports_ordinal: bool = True
    supports_full_probabilities: bool = False
    supports_confidence: bool = False
    supports_usage: bool = False
    supports_image_state: bool = False
    max_candidates: int | None = None


class DecisionProvider(ABC):
    slug: str
    display_name: str

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    async def decide(self, request: NormalizedDecisionRequest) -> ProviderResult: ...

