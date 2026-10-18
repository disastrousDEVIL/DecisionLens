"""Provider response normalization tests using documented score response shapes."""

from app.providers.cloudflare_clef_flash import CloudflareClefFlashProvider
from app.providers.openai_decisions import OpenAIDecisionsProvider
from app.providers.typesafe_jev import TypeSafeJevProvider

ORDINAL_OPTIONS = ["low", "medium", "high", "critical"]
INDEXED_SCORE = {
    "type": "score",
    "score": 1.2,
    "legend": {"0": "low", "1": "medium", "2": "high", "3": "critical"},
    "probabilities": {"0": 0.1, "1": 0.6, "2": 0.3, "3": 0.0},
}


def test_jev_score_probabilities_use_supplied_level_labels() -> None:
    answer = TypeSafeJevProvider._normalize_answer("severity", INDEXED_SCORE)

    assert list(answer.probabilities or {}) == ORDINAL_OPTIONS
    assert answer.ordinal_expected_value == 1.2


def test_clef_flash_score_probabilities_use_supplied_level_labels() -> None:
    answer = CloudflareClefFlashProvider._normalize_answer("severity", INDEXED_SCORE)

    assert list(answer.probabilities or {}) == ORDINAL_OPTIONS
    assert answer.ordinal_expected_value == 1.2


def test_openai_score_probabilities_use_level_labels_not_indices() -> None:
    answer = OpenAIDecisionsProvider._normalize_answer(
        {
            "type": "score",
            "name": "severity",
            "score": 1.2,
            "probabilities": [
                {"value": 0, "label": "low", "probability": 0.1},
                {"value": 1, "label": "medium", "probability": 0.6},
                {"value": 2, "label": "high", "probability": 0.3},
                {"value": 3, "label": "critical", "probability": 0.0},
            ],
        }
    )

    assert list(answer.probabilities or {}) == ORDINAL_OPTIONS
    assert answer.ordinal_expected_value == 1.2
