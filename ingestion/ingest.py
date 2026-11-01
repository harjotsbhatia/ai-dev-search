"""Load files from data/, chunk them, embed them and store them in Postgres.

Run from the repo root:  python ingestion/ingest.py
Re-running replaces the chunks for each file, so it's safe to run repeatedly.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select  # noqa: E402

from app.db.models import Document  # noqa: E402
from app.db.session import SessionLocal, init_db  # noqa: E402
from app.rag.chunker import chunk_text  # noqa: E402
from app.rag.embeddings import create_embeddings  # noqa: E402
from ingestion.loaders import load_files  # noqa: E402


def main() -> None:
    init_db()
    files = load_files(ROOT / "data")
    with SessionLocal() as session:
        for f in files:
            chunks = chunk_text(f.text)
            embeddings = create_embeddings(chunks)
            session.execute(delete(Document).where(Document.file_path == f.file_path))
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                session.add(
                    Document(
                        source=f.source,
                        file_path=f.file_path,
                        chunk_index=i,
                        content=chunk,
                        embedding=embedding,
                        meta=f.metadata,
                    )
                )
            print(f"{f.file_path}: {len(chunks)} chunks")
        session.commit()
        total = session.scalar(select(func.count()).select_from(Document))
    print(f"Done. {total} chunks in the documents table.")


if __name__ == "__main__":
    main()
