from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

Primitive = Literal["binary", "choice", "ordinal"]


class DecisionQuestion(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    primitive: Primitive
    instructions: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    ordered: bool = False

    @model_validator(mode="after")
    def validate_options(self) -> "DecisionQuestion":
        if self.primitive == "binary" and self.options and len(self.options) != 2:
            raise ValueError("binary questions must have exactly two options when options are supplied")
        if self.primitive in {"choice", "ordinal"} and len(self.options) < 2:
            raise ValueError(f"{self.primitive} questions need at least two options")
        if self.primitive == "ordinal" and not self.ordered:
            self.ordered = True
        return self


class NormalizedDecisionRequest(BaseModel):
    request_id: str | None = None
    state: str | dict[str, Any] | list[Any]
    questions: list[DecisionQuestion] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Answer(BaseModel):
    question_id: str
    selected_option: str | None = None
    probabilities: dict[str, float] | None = None
    confidence: float | None = None
    ordinal_expected_value: float | None = None


class ProviderResult(BaseModel):
    provider: str
    model: str | None = None
    answers: list[Answer] = Field(default_factory=list)
    latency_ms_e2e: float
    usage: dict[str, Any] | None = None
    estimated_cost_usd: float | None = None
    raw_response: dict[str, Any] | list[Any] | str | None = None
    error: str | None = None


class CompareRequest(BaseModel):
    providers: list[str] = Field(min_length=1)
    decision: NormalizedDecisionRequest


class CompareResponse(BaseModel):
    results: list[ProviderResult]

