import hashlib
import math
import re

from app.config import EMBEDDING_DIM, EMBEDDING_MODEL, EMBEDDING_PROVIDER

_client = None


def _openai_client():
    global _client
    if _client is None:
        from openai import OpenAI

        _client = OpenAI()  # reads OPENAI_API_KEY
    return _client


def _hash_embedding(text: str) -> list[float]:
    """Offline fallback: hashed bag of words, L2-normalised.

    Only matches shared words (no real semantics), but lets you run the whole
    pipeline without an API key.
    """
    vec = [0.0] * EMBEDDING_DIM
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % EMBEDDING_DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def create_embeddings(texts: list[str]) -> list[list[float]]:
    if EMBEDDING_PROVIDER == "hash":
        return [_hash_embedding(t) for t in texts]
    response = _openai_client().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def create_embedding(text: str) -> list[float]:
    return create_embeddings([text])[0]
