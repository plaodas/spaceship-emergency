"""Score cited/primary/rejected/measurements for the 15 compose queries.

The process fails only when Q01 misses a required id or promotes an avoid id.
"""

import os
import sys

from shipdiag.diagnose import GENERATION_MODELS
from shipdiag.eval_compose import load_gold
from shipdiag.gate import DATA, MODEL_FILE
from shipdiag.index import index_faults, persistent_client
from shipdiag.ollama import DEFAULT_HOST, embedder, generate, listed_models, model_present, ollama_ready
from shipdiag.prompt import render
from shipdiag.retrieve import SEED_LIMIT, assemble, clause_seeds
from shipdiag.validate import load_corpus, validate_corpus
from shipdiag.verdict import parse_verdict, verdict_issues

CHROMA_PATH = DATA / "chroma"


def evaluate(host, model, faults, couplings, embed, collection):
    rows = []
    for item in load_gold():
        query = item["query"]
        hits = clause_seeds(query, embed, collection, limit=SEED_LIMIT)
        cluster = assemble(faults, couplings, [card_id for card_id, _distance in hits])
        system, user = render(query, cluster["items"], cluster["mode"])
        try:
            text = generate(host, model, system, user)
        except Exception as exc:
            rows.append({"id": item["id"], "issues": [str(exc)]})
            continue
        issues = verdict_issues(parse_verdict(text), list(item["required"]), list(item.get("avoid") or []))
        rows.append({"id": item["id"], "issues": issues})
    return rows


def main():
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    faults, couplings = load_corpus(DATA)
    issues = validate_corpus(faults, couplings, complete=True)
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    if not ollama_ready(host):
        print(f"Ollama が {host} で応答しません。", file=sys.stderr)
        return 1
    names = listed_models(host)
    generation = next((candidate for candidate in GENERATION_MODELS if model_present(names, candidate)), None)
    if generation is None:
        print("生成モデルが無いので採点しません。", file=sys.stderr)
        return 1
    embed_model = MODEL_FILE.read_text(encoding="utf-8").strip()
    embed = embedder(host, embed_model)
    collection = index_faults(faults, embed, persistent_client(CHROMA_PATH), embed_model)
    rows = evaluate(host, generation, faults, couplings, embed, collection)
    print("id issues")
    failed = False
    for row in rows:
        print(f"{row['id']} {'; '.join(row['issues']) or '-'}")
        if row["id"] == "Q01" and row["issues"]:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
