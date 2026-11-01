from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import EMBEDDING_DIM


# Full-text search input: file path + content, with camelCase split so
# "RewardExpirationService" also matches "reward" and "expiration".
SEARCH_VECTOR_SQL = (
    "to_tsvector('english', regexp_replace(file_path || ' ' || content, "
    "'([a-z])([A-Z])', '\\1 \\2', 'g'))"
)


class Base(DeclarativeBase):
    pass


class Document(Base):
    """One chunk of one source file, plus its embedding."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)  # docs | incidents | code
    file_path: Mapped[str] = mapped_column(String(512), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    # "metadata" is reserved on SQLAlchemy models, so the attribute is meta
    meta: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    search_vector = mapped_column(TSVECTOR, Computed(SEARCH_VECTOR_SQL, persisted=True))

    __table_args__ = (Index("ix_documents_search_vector", "search_vector", postgresql_using="gin"),)
