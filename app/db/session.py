from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Enable pgvector and create tables if they don't exist."""
    from app.db.models import SEARCH_VECTOR_SQL, Base

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    # create_all doesn't add columns to an existing table, so upgrade older databases here
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS search_vector tsvector "
                f"GENERATED ALWAYS AS ({SEARCH_VECTOR_SQL}) STORED"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_documents_search_vector "
                "ON documents USING gin (search_vector)"
            )
        )


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
