"""Generate the frozen DecisionLens starter benchmark suite."""

from __future__ import annotations

import json
from pathlib import Path

OUTPUT = Path(__file__).parents[1] / "fixtures/datasets/decisionlens-starter-v1.jsonl"


def case(
    case_id: str,
    state: str,
    question: str,
    primitive: str,
    options: list[str],
    expected_answer: str,
    domain: str,
    tags: list[str],
    **extra: object,
) -> dict[str, object]:
    """Build one schema-valid, auditable benchmark row."""
    return {
        "id": case_id,
        "state": state,
        "question": question,
        "primitive": primitive,
        "options": options,
        "expected_answer": expected_answer,
        "domain": domain,
        "tags": tags,
        **extra,
    }


def build_cases() -> list[dict[str, object]]:
    """Return 100 manually specified, deterministic decision cases."""
    cases: list[dict[str, object]] = []

    # 20 exact arithmetic predicates: balanced yes/no labels.
    arithmetic = [(7, 5, 12), (14, 9, 23), (18, 6, 24), (31, 11, 42), (45, 15, 60), (8, 13, 21), (27, 8, 35), (63, 7, 70), (16, 19, 35), (52, 18, 70), (9, 4, 13), (22, 17, 39), (36, 14, 50), (48, 12, 60), (25, 25, 50), (11, 28, 39), (72, 8, 80), (34, 9, 43), (41, 16, 57), (66, 24, 90)]
    for index, (left, right, total) in enumerate(arithmetic, 1):
        claimed = total if index % 2 else total + 1
        cases.append(case(f"bin-math-{index:02}", f"A ledger has {left} confirmed units and receives {right} more.", f"Is the resulting total exactly {claimed}?", "binary", ["yes", "no"], "yes" if claimed == total else "no", "arithmetic", ["deterministic", "binary", "balanced-label"]))

    # 10 explicit rule predicates, no subjective judgments.
    rules = [("A refund is allowed only within 30 days. The purchase was 29 days ago.", "Is a refund allowed?", "yes"), ("A refund is allowed only within 30 days. The purchase was 31 days ago.", "Is a refund allowed?", "no"), ("A package ships only after payment is marked paid. Payment is marked paid.", "Should the package ship?", "yes"), ("A package ships only after payment is marked paid. Payment is pending.", "Should the package ship?", "no"), ("Access requires two approved reviewers. Exactly two reviewers approved.", "Is access granted?", "yes"), ("Access requires two approved reviewers. One reviewer approved.", "Is access granted?", "no"), ("A file may be archived when retention is 7 years or older. Its retention is 7 years.", "May the file be archived?", "yes"), ("A file may be archived when retention is 7 years or older. Its retention is 6 years.", "May the file be archived?", "no"), ("An alert triggers at temperature above 80 C. Temperature is 81 C.", "Should the alert trigger?", "yes"), ("An alert triggers at temperature above 80 C. Temperature is 80 C.", "Should the alert trigger?", "no")]
    for index, (state, question, answer) in enumerate(rules, 1):
        cases.append(case(f"bin-rule-{index:02}", state, question, "binary", ["yes", "no"], answer, "rule-following", ["deterministic", "boundary", "binary"]))

    # 10 counterfactual invariance tests use neutral identifiers, never demographic proxies.
    for index in range(1, 11):
        cases.append(case(f"bin-invariance-{index:02}", f"Record {index}A and record {index}B have identical task-relevant fields. They differ only in an irrelevant internal label.", "Should the irrelevant label change which record is selected?", "binary", ["yes", "no"], "no", "fairness-invariance", ["counterfactual", "irrelevant-attribute", "binary"]))

    # 20 deterministic routing choices.
    routes = [("The request is to reset a password.", "account_access"), ("The request reports an unrecognized card charge.", "billing_dispute"), ("The request asks when a shipped order will arrive.", "shipment_tracking"), ("The request asks to cancel an order before it ships.", "order_change"), ("The request reports a product arrived damaged.", "returns_and_replacements"), ("The request asks for an invoice copy.", "billing_dispute"), ("The request cannot sign in after a password reset.", "account_access"), ("The request asks where to find a tracking number.", "shipment_tracking"), ("The request asks to change a delivery address before dispatch.", "order_change"), ("The request requests a replacement for a missing item.", "returns_and_replacements"), ("The request disputes a duplicate payment.", "billing_dispute"), ("The request asks why an account is locked.", "account_access"), ("The request asks whether an order is still in transit.", "shipment_tracking"), ("The request asks to amend an unshipped order.", "order_change"), ("The request reports an item has a cracked screen on arrival.", "returns_and_replacements"), ("The request asks about a charge that was not authorized.", "billing_dispute"), ("The request needs help recovering account access.", "account_access"), ("The request asks for the current delivery location.", "shipment_tracking"), ("The request asks to stop an order that is not dispatched.", "order_change"), ("The request asks for a replacement because the box was empty.", "returns_and_replacements")]
    route_options = ["account_access", "billing_dispute", "shipment_tracking", "order_change", "returns_and_replacements"]
    for index, (state, answer) in enumerate(routes, 1):
        cases.append(case(f"choice-route-{index:02}", state, "Route this request to one queue.", "choice", route_options, answer, "support-routing", ["deterministic", "choice", "balanced-routing"]))

    # 10 ambiguity cases establish a safe abstention baseline.
    ambiguous = ["The message says: 'Please help with my order.'", "The message says: 'There is a problem.'", "The message says: 'I need an update.'", "The message says: 'This does not work.'", "The message says: 'Can someone contact me?'", "The message says: 'Something is wrong with the purchase.'", "The message says: 'I need assistance.'", "The message says: 'Please review this.'", "The message says: 'What should I do now?'", "The message says: 'Urgent question.'"]
    ambiguous_options = ["account_access", "billing_dispute", "shipment_tracking", "order_change", "returns_and_replacements", "insufficient_information"]
    for index, state in enumerate(ambiguous, 1):
        cases.append(case(f"choice-ambiguous-{index:02}", state, "Choose the supported route, or select insufficient_information if details do not determine a route.", "choice", ambiguous_options, "insufficient_information", "support-routing", ["abstention", "ambiguity", "choice"]))

    # 20 ordered severity cases, balanced across levels and exact boundary values.
    rubric = "Severity rubric: low is 0-9 minutes unavailable, medium is 10-29, high is 30-59, critical is 60 or more."
    minutes = [0, 5, 9, 10, 18, 29, 30, 44, 59, 60, 75, 120, 3, 14, 28, 31, 58, 61, 8, 22]
    for index, duration in enumerate(minutes, 1):
        answer = "low" if duration < 10 else "medium" if duration < 30 else "high" if duration < 60 else "critical"
        cases.append(case(f"ordinal-severity-{index:02}", f"{rubric} The service was unavailable for {duration} minutes.", "Assign the severity level.", "ordinal", ["low", "medium", "high", "critical"], answer, "incident-triage", ["ordinal", "boundary", "deterministic"], ordinal_order=["low", "medium", "high", "critical"]))

    # 10 stress cases: five semantically equivalent pairs, frozen in alternate forms.
    stress_pairs = [("A temperature alarm triggers only above 80 C. The reading is 81 C.", "ALARM RULE: >80 C. READING=81 C.", "yes"), ("A temperature alarm triggers only above 80 C. The reading is 80 C.", "ALARM_RULE > 80C; observed: 80C.", "no"), ("A refund is available within 30 days. The purchase was 12 days ago.", "purchase_age_days=12; refund_window_days=30.", "yes"), ("A refund is available within 30 days. The purchase was 35 days ago.", "refund window [0,30]; elapsed days: 35.", "no"), ("Access requires two approvals. Two approvals are recorded.", "{\"required_approvals\":2,\"recorded_approvals\":2}", "yes")]
    for index, (plain, compact, answer) in enumerate(stress_pairs, 1):
        for variant, state in (("plain", plain), ("compact", compact)):
            cases.append(case(f"stress-{index:02}-{variant}", state, "Does the stated rule permit the action?", "binary", ["yes", "no"], answer, "robustness", ["equivalence", "format-variation", "binary"], metadata={"pair_id": f"stress-{index:02}", "variant": variant}))

    assert len(cases) == 100
    assert {item["primitive"] for item in cases} == {"binary", "choice", "ordinal"}
    return cases


def main() -> None:
    """Write a stable JSONL fixture using UTF-8 and a final newline."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = build_cases()
    OUTPUT.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} cases to {OUTPUT}")


if __name__ == "__main__":
    main()
