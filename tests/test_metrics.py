from evals.metrics import dedupe, hit_at_k, recall_at_k, reciprocal_rank

RANKED = ["a.md", "b.java", "c.md"]


def test_dedupe_keeps_first_seen_order():
    assert dedupe(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_hit_at_k():
    assert hit_at_k(RANKED, {"b.java"}, 1) == 0.0
    assert hit_at_k(RANKED, {"b.java"}, 2) == 1.0


def test_recall_at_k_counts_fraction_of_relevant_found():
    assert recall_at_k(RANKED, {"a.md", "z.md"}, 3) == 0.5
    assert recall_at_k(RANKED, {"a.md", "c.md"}, 3) == 1.0


def test_reciprocal_rank_uses_first_relevant_hit():
    assert reciprocal_rank(RANKED, {"c.md", "b.java"}) == 0.5
    assert reciprocal_rank(RANKED, {"z.md"}) == 0.0
