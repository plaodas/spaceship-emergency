"""HTTP client for an already running Ollama."""

import json
import sys
import urllib.error
import urllib.request

DEFAULT_HOST = "http://127.0.0.1:11434"


def ollama_ready(host):
    try:
        get_json(host, "/api/tags", timeout=3)
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
    return True


def listed_models(host):
    tags = get_json(host, "/api/tags", timeout=10)
    return [item.get("name", "") for item in tags.get("models", [])]


def model_present(names, model):
    return any(name == model or name.startswith(model + ":") for name in names)


def ensure_model(host, model):
    if model_present(listed_models(host), model):
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


def generate(host, model, system, user):
    request = urllib.request.Request(
        host + "/api/chat",
        data=json.dumps(
            {
                "model": model,
                "stream": True,
                "think": False,
                "options": {"num_predict": 1400},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    chunks = []
    with urllib.request.urlopen(request, timeout=900) as response:
        for raw in response:
            line = raw.decode().strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get("error"):
                raise RuntimeError(event["error"])
            piece = (event.get("message") or {}).get("content") or ""
            if piece:
                chunks.append(piece)
            if event.get("done"):
                break
    content = "".join(chunks).strip()
    if not content:
        raise RuntimeError(f"{model} の /api/chat が本文を返しませんでした。")
    return content


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
