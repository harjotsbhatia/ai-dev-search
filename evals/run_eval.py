"""Score retrieval quality against the labeled questions in evals/questions.jsonl.

Run from the repo root (Postgres up, data ingested):
    python evals/run_eval.py            # print scores
    python evals/run_eval.py --save     # also write evals/results/<provider>-<mode>-<timestamp>.json
    python evals/run_eval.py --mode all # compare vector, keyword and hybrid side by side
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import EMBEDDING_MODEL, EMBEDDING_PROVIDER  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.rag.retriever import SEARCH_MODES, search  # noqa: E402
from evals.metrics import dedupe, hit_at_k, recall_at_k, reciprocal_rank  # noqa: E402

QUESTIONS = ROOT / "evals" / "questions.jsonl"
RESULTS_DIR = ROOT / "evals" / "results"


def load_questions() -> list[dict]:
    return [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()]


def summarize(rows: list[dict], k: int) -> dict:
    return {
        "n": len(rows),
        "hit@1": round(mean(r["hit@1"] for r in rows), 3),
        f"hit@{k}": round(mean(r[f"hit@{k}"] for r in rows), 3),
        f"recall@{k}": round(mean(r[f"recall@{k}"] for r in rows), 3),
        "mrr": round(mean(r["rr"] for r in rows), 3),
    }


def evaluate(mode: str, k: int, save: bool) -> dict:
    rows = []
    with SessionLocal() as session:
        for q in load_questions():
            # Several chunks can come from one file, so over-fetch and collapse to files
            chunks = search(session, q["question"], top_k=k * 4, mode=mode)
            ranked = dedupe([c.file_path for c in chunks])[:k]
            relevant = set(q["relevant"])
            rows.append(
                {
                    "id": q["id"],
                    "type": q["type"],
                    "question": q["question"],
                    "relevant": q["relevant"],
                    "retrieved": ranked,
                    "hit@1": hit_at_k(ranked, relevant, 1),
                    f"hit@{k}": hit_at_k(ranked, relevant, k),
                    f"recall@{k}": recall_at_k(ranked, relevant, k),
                    "rr": reciprocal_rank(ranked, relevant),
                }
            )

    summary = {"all": summarize(rows, k)}
    for t in sorted({r["type"] for r in rows}):
        summary[t] = summarize([r for r in rows if r["type"] == t], k)

    provider = f"{EMBEDDING_PROVIDER}" + (f" ({EMBEDDING_MODEL})" if EMBEDDING_PROVIDER == "openai" else "")
    print(f"Embeddings: {provider}   mode={mode}   k={k}\n")
    cols = list(summary["all"].keys())
    print(f"{'subset':<12}" + "".join(f"{c:>12}" for c in cols))
    for name, s in summary.items():
        print(f"{name:<12}" + "".join(f"{s[c]:>12}" for c in cols))

    misses = [r for r in rows if r["rr"] < 1]
    if misses:
        print(f"\nNot ranked first ({len(misses)}):")
        for r in misses:
            top = r["retrieved"][0] if r["retrieved"] else "-"
            print(f"  {r['id']} [{r['type']}] rr={r['rr']:.2f}  {r['question']}")
            print(f"      expected {r['relevant']}, top hit {top}")

    if save:
        RESULTS_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = RESULTS_DIR / f"{EMBEDDING_PROVIDER}-{mode}-{stamp}.json"
        out.write_text(
            json.dumps(
                {"provider": provider, "mode": mode, "k": k, "summary": summary, "rows": rows},
                indent=2,
            )
        )
        print(f"\nSaved {out.relative_to(ROOT)}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--mode", choices=[*SEARCH_MODES, "all"], default="hybrid")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    modes = SEARCH_MODES if args.mode == "all" else [args.mode]
    summaries = {}
    for mode in modes:
        summaries[mode] = evaluate(mode, args.k, args.save)
        print("\n" + "=" * 72 + "\n")

    if len(modes) > 1:
        print("Comparison (all questions / paraphrase only):\n")
        cols = list(summaries[modes[0]]["all"].keys())[1:]
        print(f"{'mode':<10}" + "".join(f"{c:>20}" for c in cols))
        for mode, s in summaries.items():
            cells = [f"{s['all'][c]:.3f} / {s['paraphrase'][c]:.3f}" for c in cols]
            print(f"{mode:<10}" + "".join(f"{cell:>20}" for cell in cells))


if __name__ == "__main__":
    main()
