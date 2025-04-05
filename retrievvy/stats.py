import numpy as np


def gini(scores: list[float]) -> float:
    """
    Compute the Gini coefficient of a distribution of non-negative scores.

    Parameters
    ----------
    scores : list[float]
        A list of non-negative numeric values. Can be empty.

    Returns
    -------
    float
        Gini coefficient in [0.0, 1.0]:
        - 0.0 → perfect equality (all scores identical or all zero)
        - 1.0 → maximal inequality (one non-zero score)

    Notes
    -----
    - Returns 0.0 if `scores` is empty or sums to zero.
    - Runtime complexity is O(n log n) due to sorting.
    """
    scores = np.array(scores)
    if np.any(scores < 0):
        raise ValueError("Scores must be non-negative")

    if len(scores) == 0:
        return 0

    scores_sorted = np.sort(scores)

    n = len(scores_sorted)
    cumulative_scores = np.cumsum(scores_sorted)
    total = cumulative_scores[-1]
    if total == 0:
        return 0.0

    return float((n + 1 - 2 * np.sum(cumulative_scores) / total) / n)


def range(scores: list[float]) -> float:
    arr = np.asarray(scores, dtype=np.float64)
    return float(np.max(arr) - np.min(arr))


def avg_gap(scores: list[float]) -> float:
    arr = np.asarray(scores, dtype=np.float64)
    if len(arr) < 2:
        return 0.0
    sorted_arr = np.sort(arr)
    gaps = np.diff(sorted_arr)
    return float(np.mean(gaps))
