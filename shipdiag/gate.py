"""Embedding gate for Q01. Talks to an already running Ollama."""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from shipdiag.index import index_faults, persistent_client, search
from shipdiag.validate import load_corpus, validate_corpus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHROMA_PATH = DATA / "chroma"
MODEL_FILE = ROOT / "embedding_model.txt"
Q01 = "最近ワープ直後だけ機体の右側が熱くなる。燃費も悪化した。"
CANDIDATES = ("bge-m3", "qwen3-embedding:4b")
PASS_RANK = 3
DEFAULT_HOST = "http://127.0.0.1:11434"


def main():
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    faults, _couplings = load_corpus(DATA)
    issues = validate_corpus(faults, _couplings, complete=False)
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1
    if not ollama_ready(host):
        print(
            f"Ollama が {host} で応答しません。関門は実行せず、embedding_model.txt は作りません。",
            file=sys.stderr,
        )
        return 1

    client = persistent_client(CHROMA_PATH)
    for model in CANDIDATES:
        ensure_model(host, model)
        embed = embedder(host, model)
        collection = index_faults(faults, embed, client, model)
        hits = search(collection, embed([Q01])[0], k=len(faults))
        print(f"model {model}")
        for rank, (card_id, distance) in enumerate(hits, start=1):
            print(f"{rank} {card_id} {distance:.4f}")
        rank = next((i for i, (card_id, _) in enumerate(hits, start=1) if card_id == "FLT-017"), None)
        if rank is not None and rank <= PASS_RANK:
            MODEL_FILE.write_text(model + "\n", encoding="utf-8")
            print(f"passed with {model} at rank {rank}")
            return 0
    print("FLT-017 はどちらのモデルでも3位以内に入りませんでした。", file=sys.stderr)
    return 1


def ollama_ready(host):
    try:
        get_json(host, "/api/tags", timeout=3)
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
    return True


def ensure_model(host, model):
    tags = get_json(host, "/api/tags", timeout=10)
    names = [item.get("name", "") for item in tags.get("models", [])]
    if any(name == model or name.startswith(model + ":") for name in names):
        return
    request = urllib.request.Request(
        host + "/api/pull",
        data=json.dumps({"model": model}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=1800) as response:
        for raw in response:
            line = raw.decode().strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get("error"):
                raise RuntimeError(event["error"])
            status = event.get("status")
            if status:
                print(status, file=sys.stderr)


def embedder(host, model):
    def embed(texts):
        payload = post_json(host, "/api/embed", {"model": model, "input": texts}, timeout=300)
        vectors = payload.get("embeddings")
        if not vectors:
            raise RuntimeError(f"{model} の /api/embed がベクトルを返しませんでした。")
        return vectors

    return embed


def get_json(host, path, timeout):
    with urllib.request.urlopen(host + path, timeout=timeout) as response:
        return json.load(response)


def post_json(host, path, payload, timeout):
    request = urllib.request.Request(
        host + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


if __name__ == "__main__":
    sys.exit(main())
