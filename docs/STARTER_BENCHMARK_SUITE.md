# DecisionLens starter benchmark suite v1

`fixtures/datasets/decisionlens-starter-v1.jsonl` contains 100 frozen cases for a local, reproducible smoke benchmark. It is not a public leaderboard and must not be presented as one.

## Coverage

| Area | Cases | What it checks |
| --- | ---: | --- |
| Exact arithmetic | 20 | Balanced true/false predicates |
| Explicit rules | 10 | Threshold and boundary following |
| Invariance | 10 | Irrelevant neutral labels must not affect a decision |
| Support routing | 20 | Deterministic multi-class routing |
| Ambiguity | 10 | Correct abstention to `insufficient_information` |
| Severity | 20 | Ordered levels and threshold boundaries |
| Robustness | 10 | Equivalent plain, compact, and JSON-like state formats |

## Bias safeguards

- Every expected answer follows an explicit rule in the row; none depends on a model opinion.
- The suite does not encode demographic categories, real names, dialects, disability, nationality, gender, religion, age, or proxies as decision features.
- Its counterfactual checks use neutral internal identifiers and assert that irrelevant labels do not change the outcome.
- Labels and options are balanced where possible. The routing set is balanced across its five classes; the ambiguity set establishes an explicit abstention baseline.
- This suite evaluates bounded decision behavior only. It does not validate fairness in real hiring, lending, medical, legal, or other high-impact decisions.

## Reproducibility

Generate the fixture with:

```bash
python scripts/generate_starter_suite.py
```

Do not change case labels in place. Create a new versioned fixture for revisions, record its hash, and compare like-for-like runs only.
