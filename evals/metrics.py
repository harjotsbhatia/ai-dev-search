"""Retrieval metrics over a ranked list of file paths."""


def dedupe(ranked: list[str]) -> list[str]:
    """Collapse chunk-level results to files, keeping first-seen order."""
    seen = set()
    return [f for f in ranked if not (f in seen or seen.add(f))]


def hit_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """1.0 if any relevant file is in the top k, else 0.0."""
    return 1.0 if relevant & set(ranked[:k]) else 0.0


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the relevant files that appear in the top k."""
    return len(relevant & set(ranked[:k])) / len(relevant)


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    """1 / position of the first relevant file, or 0.0 if none is found."""
    for i, f in enumerate(ranked, start=1):
        if f in relevant:
            return 1 / i
    return 0.0
