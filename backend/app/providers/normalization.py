"""Helpers that convert provider-specific decisions into shared answer shapes."""

from typing import Any


def normalize_score_probabilities(
    probabilities: dict[str, Any] | None,
    legend: dict[str, Any] | None,
) -> dict[str, float] | None:
    """Replace score-level indices with their human-readable labels.

    Jev-compatible score responses use ordinal indices (``"0"``, ``"1"``)
    as probability keys and include a legend mapping those indices to the
    levels supplied in the request. The benchmark scorer uses those level
    labels, so adapt the response at the provider boundary.
    """
    if not probabilities:
        return None
    return {
        str((legend or {}).get(str(index), index)): float(probability)
        for index, probability in probabilities.items()
    }
