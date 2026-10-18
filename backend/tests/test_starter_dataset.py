"""Contract checks for the versioned starter benchmark fixture."""

import json
import re
from collections import Counter
from pathlib import Path

FIXTURES = Path(__file__).parents[2] / "fixtures/datasets"


def read_dataset(version: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in (FIXTURES / f"decisionlens-starter-{version}.jsonl").read_text(encoding="utf-8").splitlines()]


def test_starter_v1_remains_a_valid_100_case_reference() -> None:
    rows = read_dataset("v1")

    assert len(rows) == 100
    assert len({row["id"] for row in rows}) == 100
    assert Counter(row["primitive"] for row in rows) == {
        "binary": 50,
        "choice": 30,
        "ordinal": 20,
    }
    assert all(row["expected_answer"] in row["options"] for row in rows)
    assert all({"id", "state", "question", "primitive", "options", "expected_answer"} <= row.keys() for row in rows)


def test_starter_v2_has_300_unique_balanced_cases() -> None:
    rows = read_dataset("v2")

    assert len(rows) == 300
    assert len({row["id"] for row in rows}) == 300
    assert Counter(row["primitive"] for row in rows) == {
        "binary": 150,
        "choice": 90,
        "ordinal": 60,
    }
    binary_labels = Counter(row["expected_answer"] for row in rows if row["primitive"] == "binary")
    ordinal_labels = Counter(row["expected_answer"] for row in rows if row["primitive"] == "ordinal")
    assert abs(binary_labels["yes"] - binary_labels["no"]) <= 2
    assert max(ordinal_labels.values()) - min(ordinal_labels.values()) <= 2
    assert len({(row["state"], row["question"]) for row in rows}) == 300
    assert all(row["expected_answer"] in row["options"] for row in rows)


def test_starter_v2_wording_pairs_are_complete_and_labeled_consistently() -> None:
    rows = read_dataset("v2")
    pairs: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        metadata = row.get("metadata", {})
        if isinstance(metadata, dict) and "pair_id" in metadata:
            pairs.setdefault(str(metadata["pair_id"]), []).append(row)

    assert len(pairs) == 15
    assert all(len(pair) == 2 and len({row["expected_answer"] for row in pair}) == 1 for pair in pairs.values())


def test_starter_v2_ordinal_labels_match_their_stated_rubrics() -> None:
    rows = read_dataset("v2")
    availability = [row for row in rows if str(row["id"]).startswith("ordinal-availability-")]
    risk = [row for row in rows if str(row["id"]).startswith("ordinal-risk-")]

    for row in availability:
        minutes = int(re.search(r"duration: (\d+) minutes", str(row["state"])).group(1))
        expected = "low" if minutes < 10 else "medium" if minutes < 30 else "high" if minutes < 60 else "critical"
        assert row["expected_answer"] == expected
    for row in risk:
        score = int(re.search(r"score: (\d+)", str(row["state"])).group(1))
        expected = "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
        assert row["expected_answer"] == expected
