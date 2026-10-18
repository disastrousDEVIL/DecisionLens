"""Generate the versioned 300-case DecisionLens starter benchmark."""

import json
from pathlib import Path


OPTIONS = ["low", "medium", "high", "critical"]
ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "fixtures/datasets/decisionlens-starter-v2.jsonl"


def case(identifier, state, question, primitive, options, expected, domain, tags, metadata=None):
    return {
        "id": identifier,
        "state": state,
        "question": question,
        "primitive": primitive,
        "options": options,
        "expected_answer": expected,
        "domain": domain,
        "tags": tags,
        **({"metadata": metadata} if metadata else {}),
    }


def build_cases():
    rows = []
    # 30 arithmetic: balanced yes/no, addition and multiplication.
    for index in range(30):
        left, right = 7 + index * 3, 2 + (index % 9)
        total = left + right if index % 2 == 0 else left * right
        expected = "yes" if index % 2 == 0 else "no"
        claimed = total if expected == "yes" else total + 1
        operation = "sum" if index % 2 == 0 else "product"
        rows.append(case(f"binary-arithmetic-{index + 1:03}", f"Values: {left} and {right}.", f"Is their {operation} exactly {claimed}?", "binary", ["yes", "no"], expected, "arithmetic", ["deterministic", "binary", operation]))
    # 30 explicit policy decisions: balanced yes/no.
    for index in range(30):
        limit, observed = 10 + index, 10 + index + (0 if index % 2 == 0 else 1)
        expected = "yes" if index % 2 == 0 else "no"
        rows.append(case(f"binary-policy-{index + 1:03}", f"Policy: approve only when the verified count is at least {limit}. Verified count: {observed}.", "Does the policy permit approval?", "binary", ["yes", "no"], expected, "rule-following", ["deterministic", "binary", "policy"]))
    # 30 boundary comparisons: balanced yes/no and distinct from policy language.
    for index in range(30):
        lower, upper = 100 + index * 5, 120 + index * 5
        observed = upper if index % 2 == 0 else upper + 1
        expected = "yes" if index % 2 == 0 else "no"
        rows.append(case(f"binary-range-{index + 1:03}", f"Accepted measurements are from {lower} through {upper}, inclusive. Recorded measurement: {observed}.", "Is the measurement within the accepted range?", "binary", ["yes", "no"], expected, "boundary-checks", ["deterministic", "binary", "boundary"]))
    # 30 materially different invariance checks, balanced across answer direction.
    irrelevant = ["display color", "archive folder", "record UUID", "import batch", "editor initials", "table row", "source filename", "UI theme", "export timestamp", "storage region", "note color", "sort position", "dashboard tab", "case nickname", "report font", "attachment order", "internal alias", "calendar color", "notification channel", "cache key", "view mode", "workspace label", "sync timestamp", "column order", "device name", "audit sequence", "thumbnail style", "template name", "release label", "log prefix"]
    for index, field in enumerate(irrelevant):
        expected = "yes" if index % 2 == 0 else "no"
        question = (
            f"Should selection remain unchanged when only {field} changes?"
            if expected == "yes"
            else f"Should {field} change which record is selected?"
        )
        rows.append(case(f"binary-invariance-{index + 1:03}", f"Selection policy uses only severity=high and impact=customer-facing. Both records have severity=high and impact=customer-facing; they differ only in {field}.", question, "binary", ["yes", "no"], expected, "invariance", ["invariance", "binary", "irrelevant-field"]))
    # 30 paired wording checks: 15 rules expressed in plain and compact forms.
    for index in range(15):
        threshold = 20 + index * 4
        observed = threshold if index % 2 == 0 else threshold - 1
        expected = "yes" if index % 2 == 0 else "no"
        pair_id = f"wording-{index + 1:02}"
        rows.extend([
            case(f"binary-wording-{index + 1:02}-plain", f"A review passes when its score is at least {threshold}. The score is {observed}.", "Does the rule permit the action?", "binary", ["yes", "no"], expected, "robustness", ["equivalence", "binary", "plain"], {"pair_id": pair_id, "variant": "plain"}),
            case(f"binary-wording-{index + 1:02}-compact", f"pass_if=score>={threshold}; score={observed}.", "Does the rule permit the action?", "binary", ["yes", "no"], expected, "robustness", ["equivalence", "binary", "compact"], {"pair_id": pair_id, "variant": "compact"}),
        ])
    # 90 fixed-choice routing decisions across three domains.
    route_sets = [
        ("support-routing", ["billing", "technical", "account", "shipping", "security"], ["subscription charge", "login reset", "delivery delay", "suspicious sign-in", "integration error"]),
        ("operations-routing", ["on-call", "database", "network", "release", "observability"], ["service timeout", "slow query", "packet loss", "rollback request", "missing alert"]),
        ("content-routing", ["news", "tutorial", "reference", "policy", "announcement"], ["event report", "step-by-step setup", "parameter definition", "usage restriction", "release notice"]),
    ]
    for domain, options, topics in route_sets:
        for index in range(30):
            expected = options[index % len(options)]
            topic = topics[index % len(topics)]
            rows.append(case(f"choice-{domain}-{index + 1:03}", f"Request {index + 1}: {topic}. Route it to the team or content type that owns this issue.", "Choose the single best destination.", "choice", options, expected, domain, ["choice", "routing", "balanced-label"]))
    # 60 ordinal cases using explicit rubrics and balanced four-level labels.
    for index in range(30):
        level_index = index % 4
        minutes = [2, 12, 35, 65][level_index] + (index // 4)
        rows.append(case(f"ordinal-availability-{index + 1:03}", f"Severity rubric: low=0-9 minutes unavailable; medium=10-29; high=30-59; critical=60+. Outage duration: {minutes} minutes.", "Assign the severity level.", "ordinal", OPTIONS, OPTIONS[level_index], "incident-triage", ["ordinal", "boundary", "availability"]))
    for index in range(30):
        level_index = index % 4
        value = [10, 35, 65, 90][level_index] + (index // 4)
        rows.append(case(f"ordinal-risk-{index + 1:03}", f"Risk rubric: low=0-24; medium=25-49; high=50-74; critical=75-100. Assessed risk score: {value}.", "Assign the risk level.", "ordinal", OPTIONS, OPTIONS[level_index], "risk-assessment", ["ordinal", "boundary", "risk"]))
    assert len(rows) == 300
    return rows


def main():
    rows = build_cases()
    OUTPUT.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
