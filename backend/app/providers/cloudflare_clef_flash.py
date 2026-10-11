import time
from typing import Any

import httpx

from app.core.config import Settings
from app.providers.base import DecisionProvider, ProviderCapabilities
from app.schemas.decisions import Answer, NormalizedDecisionRequest, ProviderResult


class CloudflareClefFlashProvider(DecisionProvider):
    slug = "clef-flash"
    display_name = "Cloudflare Clef-flash"

    def __init__(self, settings: Settings):
        self.settings = settings

    def is_available(self) -> bool:
        return bool(self.settings.cloudflare_account_id and self.settings.cloudflare_api_token)

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_full_probabilities=True,
            supports_confidence=True,
            supports_usage=True,
            supports_image_state=True,
            max_candidates=None,
        )

    async def decide(self, request: NormalizedDecisionRequest) -> ProviderResult:
        started = time.perf_counter()
        if not self.is_available():
            return ProviderResult(provider=self.slug, latency_ms_e2e=0, error="Provider is not configured")

        questions: dict[str, dict[str, Any]] = {}
        for question in request.questions:
            question_type = {"binary": "noul", "choice": "choice", "ordinal": "score"}[question.primitive]
            item: dict[str, Any] = {"type": question_type, "instructions": question.instructions}
            if question_type == "choice":
                item["criteria"] = {option: None for option in question.options}
            elif question_type == "score":
                item["criteria"] = question.options
            questions[question.id] = item

        body = {"model": "clef-flash", "state": request.state, "questions": questions}
        path = f"/client/v4/accounts/{self.settings.cloudflare_account_id}/ai/run/@cf/cloudflare/clef-flash"
        try:
            async with httpx.AsyncClient(base_url="https://api.cloudflare.com", timeout=30) as client:
                response = await client.post(path, headers={"Authorization": f"Bearer {self.settings.cloudflare_api_token}"}, json=body)
                response.raise_for_status()
                envelope = response.json()
                data = envelope.get("result", envelope)
        except httpx.HTTPError as exc:
            return ProviderResult(provider=self.slug, latency_ms_e2e=(time.perf_counter() - started) * 1000, error=str(exc))

        answers = [self._normalize_answer(question_id, answer) for question_id, answer in data.get("answers", {}).items()]
        return ProviderResult(provider=self.slug, model=data.get("model", "clef-flash"), answers=answers, latency_ms_e2e=(time.perf_counter() - started) * 1000, usage=data.get("usage"), raw_response=envelope)

    @staticmethod
    def _normalize_answer(question_id: str, answer: dict[str, Any]) -> Answer:
        probabilities = answer.get("probabilities")
        selected = answer.get("choice")
        if "noul" in answer:
            probability = float(answer["noul"])
            probabilities = {"yes": probability, "no": 1 - probability}
            selected = "yes" if probability >= 0.5 else "no"
        return Answer(question_id=question_id, selected_option=selected, probabilities=probabilities, confidence=answer.get("confidence"), ordinal_expected_value=answer.get("score"))

