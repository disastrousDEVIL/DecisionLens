import time
from typing import Any

import httpx

from app.core.config import Settings
from app.providers.base import DecisionProvider, ProviderCapabilities
from app.providers.normalization import normalize_score_probabilities
from app.schemas.decisions import Answer, NormalizedDecisionRequest, ProviderResult


class TypeSafeJevProvider(DecisionProvider):
    slug = "jev"
    display_name = "TypeSafe Jev"

    def __init__(self, settings: Settings):
        self.settings = settings

    def is_available(self) -> bool:
        return bool(self.settings.typesafe_api_key)

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_full_probabilities=True,
            supports_confidence=True,
            supports_usage=True,
            max_candidates=255,
        )

    async def decide(self, request: NormalizedDecisionRequest) -> ProviderResult:
        started = time.perf_counter()
        if not self.is_available():
            return ProviderResult(provider=self.slug, latency_ms_e2e=0, error="Provider is not configured")

        questions: dict[str, dict[str, Any]] = {}
        for question in request.questions:
            question_type = {"binary": "noul", "choice": "choice", "ordinal": "score"}[question.primitive]
            payload: dict[str, Any] = {"type": question_type, "instructions": question.instructions}
            if question_type == "choice":
                payload["criteria"] = {option: None for option in question.options}
            elif question_type == "score":
                payload["criteria"] = question.options
            questions[question.id] = payload

        body = {"model": "jev-latest", "state": request.state, "questions": questions}
        try:
            async with httpx.AsyncClient(base_url=self.settings.typesafe_base_url, timeout=30) as client:
                response = await client.post(
                    "/v1/systemone",
                    headers={"Authorization": f"Bearer {self.settings.typesafe_api_key}"},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            return ProviderResult(provider=self.slug, latency_ms_e2e=(time.perf_counter() - started) * 1000, error=str(exc))

        answers = [self._normalize_answer(question_id, answer) for question_id, answer in data.get("answers", {}).items()]
        return ProviderResult(
            provider=self.slug,
            model=data.get("model"),
            answers=answers,
            latency_ms_e2e=(time.perf_counter() - started) * 1000,
            usage=data.get("usage"),
            raw_response=data,
        )

    @staticmethod
    def _normalize_answer(question_id: str, answer: dict[str, Any]) -> Answer:
        probabilities = answer.get("probabilities")
        selected = answer.get("choice") or answer.get("selected_option")
        if "noul" in answer:
            probability = float(answer["noul"])
            probabilities = {"yes": probability, "no": 1 - probability}
            selected = "yes" if probability >= 0.5 else "no"
        elif answer.get("type") == "score":
            probabilities = normalize_score_probabilities(probabilities, answer.get("legend"))
        return Answer(
            question_id=question_id,
            selected_option=selected,
            probabilities=probabilities,
            confidence=answer.get("confidence"),
            ordinal_expected_value=answer.get("score"),
        )

