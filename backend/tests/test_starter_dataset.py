"""Contract checks for the versioned starter benchmark fixture."""

import json
from collections import Counter
from pathlib import Path

DATASET = Path(__file__).parents[2] / "fixtures/datasets/decisionlens-starter-v1.jsonl"


def test_starter_suite_has_100_valid_unique_cases() -> None:
    """Keep the fixture stable, valid, and broad enough for its intended smoke run."""
    rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines()]

    assert len(rows) == 100
    assert len({row["id"] for row in rows}) == 100
    assert Counter(row["primitive"] for row in rows) == {
        "binary": 50,
        "choice": 30,
        "ordinal": 20,
    }
    assert all(row["expected_answer"] in row["options"] for row in rows)
    assert all({"id", "state", "question", "primitive", "options", "expected_answer"} <= row.keys() for row in rows)
