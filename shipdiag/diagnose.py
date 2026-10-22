"""Print the Q01 cluster, an FTS baseline, and a diagnosis when a model is present."""

import os
import sys

from shipdiag.fts import document_text, score_corpus
from shipdiag.gate import DATA, MODEL_FILE, Q01
from shipdiag.index import index_faults, persistent_client
from shipdiag.ollama import DEFAULT_HOST, embedder, generate, listed_models, model_present, ollama_ready
from shipdiag.prompt import render
from shipdiag.retrieve import SEED_LIMIT, assemble, clause_seeds
from shipdiag.validate import load_corpus, validate_corpus

CHROMA_PATH = DATA / "chroma"
REQUIRED = {"FLT-017", "FLT-044", "FLT-028", "CPL-03"}
GENERATION_MODELS = ("qwen3:8b", "qwen3:4b")


def main():
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    faults, couplings = load_corpus(DATA)
    issues = validate_corpus(faults, couplings, complete=True)
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    if not ollama_ready(host):
        print(
            f"Ollama が {host} で応答しません。クラスタは単体テストで確認し、診断文は作りません。",
            file=sys.stderr,
        )
        return 1

    embed_model = MODEL_FILE.read_text(encoding="utf-8").strip()
    embed = embedder(host, embed_model)
    collection = index_faults(faults, embed, persistent_client(CHROMA_PATH), embed_model)
    hits = clause_seeds(Q01, embed, collection, limit=SEED_LIMIT)
    print("seeds")
    for rank, (card_id, distance) in enumerate(hits, start=1):
        print(f"{rank} {card_id} {distance:.4f}")
    seed_ids = [card_id for card_id, _distance in hits]
    if "CPL-03" in seed_ids:
        print("拡張前の種に CPL-03 が入っています。", file=sys.stderr)
        return 1

    cluster = assemble(faults, couplings, seed_ids)
    print("mode", cluster["mode"])
    print("cluster")
    for item in cluster["items"]:
        print(f"{item['id']} {item['reason']}")
    ids = {item["id"] for item in cluster["items"]}
    missing = REQUIRED - ids
    if missing:
        print(f"クラスタに必要な文書がありません: {sorted(missing)}", file=sys.stderr)
        return 1
    downstream = faults["FLT-028"]["derived"]
    leaked = [card_id for card_id in downstream if card_id in ids]
    if leaked:
        print(f"FLT-028 の下流がクラスタに残っています: {leaked}", file=sys.stderr)
        return 1

    documents = [(card_id, document_text(card=card)) for card_id, card in faults.items()]
    documents.extend((note_id, document_text(note=note)) for note_id, note in couplings.items())
    scores = score_corpus(documents, Q01)
    print("fts")
    for doc_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])):
        print(f"{doc_id} {score:.4f}")

    names = listed_models(host)
    generation = next((model for model in GENERATION_MODELS if model_present(names, model)), None)
    if generation is None:
        print("生成モデルが無いので診断文は作りません。")
        return 0
    system, user = render(Q01, cluster["items"], cluster["mode"])
    print("diagnosis")
    print(generate(host, generation, system, user))
    return 0


if __name__ == "__main__":
    sys.exit(main())
