"""Cluster recall for the 15 compose queries, next to a full-text baseline."""

import os
import sys
from pathlib import Path

import yaml

from shipdiag.fts import document_text, score_corpus
from shipdiag.gate import DATA, MODEL_FILE
from shipdiag.index import index_faults, persistent_client, search
from shipdiag.ollama import DEFAULT_HOST, embedder, ollama_ready
from shipdiag.retrieve import assemble
from shipdiag.validate import load_corpus, validate_corpus

ROOT = Path(__file__).resolve().parents[1]
GOLD = DATA / "eval" / "compose.yaml"
CHROMA_PATH = DATA / "chroma"
SEED_LIMIT = 8


def load_gold(path=GOLD):
    gold = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(gold, list):
        raise RuntimeError("compose.yaml はクエリのリスト")
    return gold


def recall(required, found):
    if not required:
        return 1.0
    return len(set(required) & set(found)) / len(required)


def evaluate(host, faults, couplings, embed, collection):
    documents = [(card_id, document_text(card=card)) for card_id, card in faults.items()]
    documents.extend((note_id, document_text(note=note)) for note_id, note in couplings.items())
    rows = []
    for item in load_gold():
        query = item["query"]
        required = list(item["required"])
        hits = search(collection, embed([query])[0], k=SEED_LIMIT)
        cluster = assemble(faults, couplings, [card_id for card_id, _distance in hits])
        cluster_ids = {entry["id"] for entry in cluster}
        scores = score_corpus(documents, query)
        ranked = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
        fts_ids = {doc_id for doc_id, score in ranked[:SEED_LIMIT] if score > 0}
        cluster_recall = recall(required, cluster_ids)
        fts_recall = recall(required, fts_ids)
        rows.append(
            {
                "id": item["id"],
                "cluster_recall": cluster_recall,
                "fts_recall": fts_recall,
                "delta": cluster_recall - fts_recall,
                "missing": sorted(set(required) - cluster_ids),
                "avoid_hit": sorted(set(item.get("avoid") or []) & cluster_ids),
                "cpl03_fts": scores.get("CPL-03"),
            }
        )
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
    model = MODEL_FILE.read_text(encoding="utf-8").strip()
    embed = embedder(host, model)
    collection = index_faults(faults, embed, persistent_client(CHROMA_PATH), model)
    rows = evaluate(host, faults, couplings, embed, collection)
    print("id cluster_recall fts_recall delta missing avoid_hit")
    for row in rows:
        print(
            f"{row['id']} {row['cluster_recall']:.2f} {row['fts_recall']:.2f} "
            f"{row['delta']:+.2f} {row['missing'] or '-'} {row['avoid_hit'] or '-'}"
        )
    q01 = next(row for row in rows if row["id"] == "Q01")
    print(f"Q01 CPL-03 fts {q01['cpl03_fts']}")
    if q01["cluster_recall"] < 1 or q01["cpl03_fts"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
