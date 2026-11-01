import re
from dataclasses import dataclass, replace

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import SEARCH_MODE
from app.db.models import Document
from app.rag.embeddings import create_embedding

SEARCH_MODES = ("vector", "keyword", "hybrid")

# Standard RRF constant: dampens the gap between rank 1 and rank 2 so one list can't dominate
RRF_K = 60
# How many candidates each retriever contributes before fusion
CANDIDATES = 20


@dataclass
class SearchResult:
    id: int
    source: str
    file_path: str
    content: str
    score: float


def _to_result(doc: Document, score: float) -> SearchResult:
    return SearchResult(
        id=doc.id,
        source=doc.source,
        file_path=doc.file_path,
        content=doc.content,
        score=round(score, 4),
    )


def vector_search(session: Session, query: str, top_k: int) -> list[SearchResult]:
    """Rank chunks by cosine similarity to the query embedding."""
    query_embedding = create_embedding(query)
    distance = Document.embedding.cosine_distance(query_embedding)
    rows = session.execute(
        select(Document, distance.label("distance")).order_by(distance).limit(top_k)
    ).all()
    return [_to_result(doc, 1 - dist) for doc, dist in rows]


def build_tsquery(query: str) -> str:
    """OR together the query's words, camelCase split, for to_tsquery.

    plainto_tsquery ANDs every word, so a natural-language question rarely matches
    anything. OR-ing lets ts_rank reward chunks that match more of the words.
    """
    words = re.findall(r"[A-Za-z0-9]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", query))
    return " | ".join(words)


def keyword_search(session: Session, query: str, top_k: int) -> list[SearchResult]:
    """Rank chunks with Postgres full-text search (ts_rank, length-normalised)."""
    tsquery_text = build_tsquery(query)
    if not tsquery_text:
        return []
    tsquery = func.to_tsquery("english", tsquery_text)
    rank = func.ts_rank(Document.search_vector, tsquery, 1)
    rows = session.execute(
        select(Document, rank.label("rank"))
        .where(Document.search_vector.op("@@")(tsquery))
        .order_by(rank.desc())
        .limit(top_k)
    ).all()
    return [_to_result(doc, r) for doc, r in rows]


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]], top_k: int, k: int = RRF_K
) -> list[SearchResult]:
    """Merge ranked lists: each chunk scores sum(1 / (k + rank)) across the lists it appears in.

    Uses only ranks, so cosine similarities and ts_rank scores never need to be on the same scale.
    """
    scores: dict[int, float] = {}
    by_id: dict[int, SearchResult] = {}
    for results in result_lists:
        for rank, r in enumerate(results, start=1):
            scores[r.id] = scores.get(r.id, 0.0) + 1 / (k + rank)
            by_id.setdefault(r.id, r)
    ranked = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [replace(by_id[i], score=round(scores[i], 4)) for i in ranked]


def search(
    session: Session, query: str, top_k: int = 5, mode: str = SEARCH_MODE
) -> list[SearchResult]:
    if mode == "vector":
        return vector_search(session, query, top_k)
    if mode == "keyword":
        return keyword_search(session, query, top_k)
    if mode == "hybrid":
        n = max(CANDIDATES, top_k)
        return reciprocal_rank_fusion(
            [vector_search(session, query, n), keyword_search(session, query, n)], top_k
        )
    raise ValueError(f"unknown search mode {mode!r}, expected one of {SEARCH_MODES}")
