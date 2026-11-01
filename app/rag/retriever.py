from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document
from app.rag.embeddings import create_embedding


@dataclass
class SearchResult:
    id: int
    source: str
    file_path: str
    content: str
    score: float


def search(session: Session, query: str, top_k: int = 5) -> list[SearchResult]:
    """Embed the query and return the top_k most similar chunks by cosine similarity."""
    query_embedding = create_embedding(query)
    distance = Document.embedding.cosine_distance(query_embedding)
    rows = session.execute(
        select(Document, distance.label("distance")).order_by(distance).limit(top_k)
    ).all()
    return [
        SearchResult(
            id=doc.id,
            source=doc.source,
            file_path=doc.file_path,
            content=doc.content,
            score=round(1 - dist, 4),
        )
        for doc, dist in rows
    ]
