from app.config import LLM_MODEL
from app.rag.embeddings import _openai_client
from app.rag.retriever import SearchResult

SYSTEM_PROMPT = """You answer questions about a company's codebase, documentation and incidents.

Answer using only the provided context.
Every factual statement must cite one of the provided sources with its number, like [1].
If the answer is not contained in the context, say you don't know.
Be concise."""


def build_context(results: list[SearchResult]) -> str:
    blocks = [f"[{i}] {r.file_path}\n\n{r.content}" for i, r in enumerate(results, start=1)]
    return "\n\n---\n\n".join(blocks)


def build_messages(question: str, results: list[SearchResult]) -> list[dict]:
    user = f"Context:\n\n{build_context(results)}\n\nQuestion: {question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def generate_answer(question: str, results: list[SearchResult]) -> str:
    if not results:
        return "I don't know. No relevant documents were found."
    response = _openai_client().chat.completions.create(
        model=LLM_MODEL,
        messages=build_messages(question, results),
        temperature=0,
    )
    return response.choices[0].message.content
