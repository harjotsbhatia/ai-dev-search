# AI Dev Search

A plain-Python RAG system over a company's docs, incidents and code.
No LangChain: FastAPI + SQLAlchemy + pgvector + the OpenAI SDK.

```
data/ files → chunk → embed → Postgres (pgvector) → /search → /ask (LLM + citations)
```

## Setup

Requires Docker and Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set OPENAI_API_KEY
```

No API key yet? Set `EMBEDDING_PROVIDER=hash` in `.env`. Search then works offline
(keyword-ish matching, not real semantics); `/ask` still needs a key.
If you switch providers, re-run ingestion so stored embeddings match the query embeddings.

## Run

```bash
docker compose up -d
python ingestion/ingest.py
uvicorn app.main:app --reload
```

Check retrieval first:

```bash
curl "localhost:8000/search?q=Where+is+reward+expiration+calculated"
```

Then ask:

```bash
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "Where is reward expiration calculated?"}'
```

Inspect the table directly:

```bash
docker compose exec postgres psql -U rag -d rag -c "SELECT id, source, file_path, chunk_index FROM documents;"
```

## Tests

```bash
pytest
```

Unit tests don't need Postgres or an API key.

## Evaluation

`evals/questions.jsonl` holds 32 questions, each labeled with the files that should be
retrieved. `keyword` questions share words with their source; `paraphrase` questions
deliberately don't (e.g. "loyalty credits" for "reward points"), so only semantic
embeddings can find them.

```bash
python evals/run_eval.py          # print scores and the questions that missed
python evals/run_eval.py --save   # also save to evals/results/
```

Metrics (computed per file, after collapsing chunks from the same file):

| Metric | Meaning |
|---|---|
| hit@1 | Was the top result a relevant file? |
| hit@5 | Was any relevant file in the top 5? |
| recall@5 | What fraction of the relevant files were in the top 5? |
| MRR | Mean of 1 / rank of the first relevant file |

Baseline with the offline `hash` embeddings:

| subset | hit@1 | hit@5 | recall@5 | MRR |
|---|---|---|---|---|
| all (32) | 0.656 | 0.938 | 0.818 | 0.771 |
| keyword (26) | 0.731 | 1.000 | 0.872 | 0.843 |
| paraphrase (6) | 0.333 | 0.667 | 0.583 | 0.458 |

With only 11 files, any 5 results cover almost half the corpus, so hit@5 is inflated.
hit@1 and MRR are the numbers to watch until the corpus grows.

## Layout

| Path | What it does |
|---|---|
| `app/rag/chunker.py` | Fixed-size chunks with overlap |
| `app/rag/embeddings.py` | OpenAI embeddings, or the offline `hash` fallback |
| `app/rag/retriever.py` | Cosine-similarity search with pgvector |
| `app/rag/generator.py` | Numbered-context prompt, citations required |
| `app/api/search.py` | `GET /search`, `POST /ask` |
| `ingestion/` | Load `data/`, chunk, embed, store |
| `data/` | Fake company docs, incidents and Java code |
| `evals/` | Labeled questions, retrieval metrics, saved results |

## Next steps (in order)

1. Metadata filtering (e.g. `source=code`)
2. Better chunking
3. ~~Evaluation dataset~~ (done, see above)
4. BM25 + vector hybrid search
5. Reranking
6. Query rewriting
7. GitHub ingestion
8. Code-aware AST chunking
9. Graph relationships
10. Observability/deployment
