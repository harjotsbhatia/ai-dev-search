from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.rag import retriever
from app.rag.generator import generate_answer

router = APIRouter()


class SearchHit(BaseModel):
    source: str
    file: str
    score: float
    content: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHit]


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class Citation(BaseModel):
    id: int
    file: str
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[Citation]


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
    session: Session = Depends(get_session),
):
    results = retriever.search(session, q, top_k)
    return SearchResponse(
        query=q,
        results=[
            SearchHit(source=r.source, file=r.file_path, score=r.score, content=r.content)
            for r in results
        ],
    )


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, session: Session = Depends(get_session)):
    results = retriever.search(session, request.question, request.top_k)
    answer = generate_answer(request.question, results)
    return AskResponse(
        question=request.question,
        answer=answer,
        # Numbering matches the [n] markers in the prompt context
        sources=[
            Citation(id=i, file=r.file_path, score=r.score)
            for i, r in enumerate(results, start=1)
        ],
    )
