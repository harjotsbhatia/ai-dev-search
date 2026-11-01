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

## Hybrid search

`SEARCH_MODE` (or `?mode=` on `/search`, `"mode"` on `/ask`) picks the retriever:

- `vector`: cosine similarity on embeddings (pgvector)
- `keyword`: Postgres full-text search. `documents.search_vector` is a generated
  `tsvector` over file path + content, with camelCase split so `RewardExpirationService`
  matches "reward expiration". Query words are OR-ed and ranked with `ts_rank`.
- `hybrid` (default): top 20 from each, merged with Reciprocal Rank Fusion,
  `score = Σ 1 / (60 + rank)`. RRF uses only ranks, so the two retrievers' scores
  never need to be on the same scale.

```bash
python evals/run_eval.py --mode all   # compare all three
```

Results with the offline `hash` embeddings (all 32 questions / 6 paraphrase questions):

| mode | hit@1 | hit@5 | recall@5 | MRR |
|---|---|---|---|---|
| vector | 0.656 / 0.333 | 0.938 / 0.667 | 0.818 / 0.583 | 0.771 / 0.458 |
| keyword | **0.812** / **0.500** | 0.938 / 0.667 | **0.896** / 0.583 | **0.862** / **0.542** |
| hybrid | 0.719 / 0.167 | **1.000** / **1.000** | 0.880 / **0.833** | 0.852 / **0.542** |

Reading these honestly:

- Full-text search beats `hash` vectors outright. It stems words ("expires" ↔ "expiration"),
  drops stopwords and splits camelCase; the hash embedding does none of that.
- Hybrid is the only mode that gets a relevant file into the top 5 for every question,
  but fusing in the weaker vector list costs it hit@1 against keyword alone.
- The `hash` "vector" retriever is itself just word matching, so this fuses two lexical
  signals. Hybrid's real test is with semantic embeddings, where the two retrievers fail
  on different questions. Re-run with `EMBEDDING_PROVIDER=openai`.
- The paraphrase subset is 6 questions; one question moves its scores by 0.167.

## Layout

| Path | What it does |
|---|---|
| `app/rag/chunker.py` | Fixed-size chunks with overlap |
| `app/rag/embeddings.py` | OpenAI embeddings, or the offline `hash` fallback |
| `app/rag/retriever.py` | Vector, full-text and hybrid (RRF) search |
| `app/rag/generator.py` | Numbered-context prompt, citations required |
| `app/api/search.py` | `GET /search`, `POST /ask` |
| `ingestion/` | Load `data/`, chunk, embed, store |
| `data/` | Fake company docs, incidents and Java code |
| `evals/` | Labeled questions, retrieval metrics, saved results |

## Next steps (in order)

1. Metadata filtering (e.g. `source=code`)
2. Better chunking
3. ~~Evaluation dataset~~ (done, see above)
4. ~~BM25 + vector hybrid search~~ (done with Postgres full-text + RRF, see above)
5. Reranking
6. Query rewriting
7. GitHub ingestion
8. Code-aware AST chunking
9. Graph relationships
10. Observability/deployment
