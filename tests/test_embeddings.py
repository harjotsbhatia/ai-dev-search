import math

from app.rag.embeddings import _hash_embedding


def test_hash_embedding_is_normalised_and_deterministic():
    a = _hash_embedding("reward expiration")
    assert a == _hash_embedding("reward expiration")
    assert math.isclose(sum(v * v for v in a), 1.0)
