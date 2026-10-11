import json
import time
from typing import Any

import httpx

from app.core.config import Settings
from app.providers.base import DecisionProvider, ProviderCapabilities
from app.schemas.decisions import Answer, NormalizedDecisionRequest, ProviderResult


class OpenAIDecisionsProvider(DecisionProvider):
    slug = "openai-decisions"
    display_name = "OpenAI Decisions"

    def __init__(self, settings: Settings):
        self.settings = settings

    def is_available(self) -> bool:
        return bool(self.settings.openai_api_key and self.settings.openai_decisions_enabled)

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_full_probabilities=True,
            supports_confidence=True,
            supports_usage=True,
            supports_image_state=True,
        )

    async def decide(self, request: NormalizedDecisionRequest) -> ProviderResult:
        started = time.perf_counter()
        if not self.is_available():
            return ProviderResult(provider=self.slug, latency_ms_e2e=0, error="Provider is not configured or enabled")

        questions: list[dict[str, Any]] = []
        for question in request.questions:
            question_type = {"binary": "predicate", "choice": "choice", "ordinal": "score"}[question.primitive]
            item: dict[str, Any] = {"type": question_type, "name": question.id, "instructions": question.instructions}
            if question_type == "choice":
                item["choices"] = [{"value": option} for option in question.options]
            elif question_type == "score":
                item["levels"] = [{"label": option} for option in question.options]
            questions.append(item)

        input_value = request.state if isinstance(request.state, str) else json.dumps(request.state)
        body = {"model": "gpt-6-luna", "input": input_value, "questions": questions}
        try:
            async with httpx.AsyncClient(base_url="https://api.openai.com", timeout=30) as client:
                response = await client.post(
                    "/v1/decisions",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            return ProviderResult(provider=self.slug, latency_ms_e2e=(time.perf_counter() - started) * 1000, error=str(exc))

        answers = [self._normalize_answer(answer) for answer in data.get("answers", [])]
        return ProviderResult(provider=self.slug, model=data.get("model"), answers=answers, latency_ms_e2e=(time.perf_counter() - started) * 1000, usage=data.get("usage"), raw_response=data)

    @staticmethod
    def _normalize_answer(answer: dict[str, Any]) -> Answer:
        probabilities = {
            str(item.get("value", item.get("label"))): float(item["probability"])
            for item in answer.get("probabilities", [])
        } or None
        if answer.get("type") == "predicate":
            probability = float(answer.get("probability", 0))
            probabilities = {"yes": probability, "no": 1 - probability}
        return Answer(question_id=answer.get("name", "unknown"), selected_option=answer.get("choice"), probabilities=probabilities, confidence=answer.get("confidence"), ordinal_expected_value=answer.get("score"))
