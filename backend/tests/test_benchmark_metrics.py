"""Unit tests for benchmark calculations without paid provider calls."""

from pytest import approx

from app.api.v1.routes.benchmarks import metrics


def result(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "provider": "jev",
        "expected": "low",
        "selected": "low",
        "probabilities": None,
        "latency_ms": 100.0,
        "error": None,
        "tags": [],
        "domain": "incident",
        "primitive": "ordinal",
        "candidate_count": 4,
        "case_id": "case-1",
        "options": ["low", "medium", "high", "critical"],
        "metadata": {},
        "usage": {"input_tokens": 100, "output_tokens": 0},
    }
    row.update(overrides)
    return row


def test_ordinal_label_is_scored_without_probabilities() -> None:
    summary = metrics([result()], ["jev"])

    provider = summary["providers"]["jev"]
    assert provider["accuracy"] == 1.0
    assert provider["invalid_answer_rate"] == 0.0


def test_categorical_brier_uses_every_option() -> None:
    summary = metrics(
        [
            result(
                expected="yes",
                selected="yes",
                probabilities={"yes": 0.9, "no": 0.1},
                options=["yes", "no"],
                primitive="binary",
            )
        ],
        ["jev"],
    )

    assert summary["providers"]["jev"]["brier"] == approx(0.01)
    assert summary["providers"]["jev"]["expected_calibration_error"] == approx(0.1)


def test_invalid_answer_is_not_counted_as_correct() -> None:
    summary = metrics([result(selected=None)], ["jev"])

    provider = summary["providers"]["jev"]
    assert provider["accuracy"] == 0.0
    assert provider["invalid_answer_rate"] == 1.0
