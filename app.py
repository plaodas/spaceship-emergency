"""Streamlit view of the same diagnosis path as shipdiag.diagnose."""

import os

import streamlit as st

from shipdiag.diagnose import CHROMA_PATH, GENERATION_MODELS
from shipdiag.gate import DATA, MODEL_FILE
from shipdiag.index import index_faults, persistent_client, search
from shipdiag.ollama import DEFAULT_HOST, embedder, generate, listed_models, model_present, ollama_ready
from shipdiag.prompt import render
from shipdiag.retrieve import assemble
from shipdiag.validate import load_corpus, validate_corpus

CONFOUNDER_ROLES = {"confounder", "sensor_lie"}


@st.cache_resource
def prepare(host, model):
    faults, couplings = load_corpus(DATA)
    issues = validate_corpus(faults, couplings, complete=True)
    if issues:
        raise RuntimeError("\n".join(issues))
    embed = embedder(host, model)
    collection = index_faults(faults, embed, persistent_client(CHROMA_PATH), model)
    return faults, couplings, embed, collection


def _rows(faults, pairs):
    rows = []
    for card_id, distance in pairs:
        card = faults[card_id]
        rows.append(
            {
                "id": card_id,
                "name": card["name"],
                "distance": f"{distance:.4f}",
                "role": card["role"],
            }
        )
    return rows


def main():
    st.set_page_config(page_title="宇宙船故障診断")
    st.title("宇宙船故障診断")
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    if not ollama_ready(host):
        st.error(f"Ollama が {host} で応答しません。")
        return
    model = MODEL_FILE.read_text(encoding="utf-8").strip()
    query = st.text_area("症状", height=120)
    if not st.button("診断", type="primary"):
        return
    if not query.strip():
        st.warning("症状文を入れてください。")
        return

    faults, couplings, embed, collection = prepare(host, model)
    hits = search(collection, embed([query.strip()])[0], k=8)
    seed_ids = [card_id for card_id, _distance in hits]
    plain = [(card_id, distance) for card_id, distance in hits if faults[card_id]["role"] not in CONFOUNDER_ROLES]
    confounders = [(card_id, distance) for card_id, distance in hits if faults[card_id]["role"] in CONFOUNDER_ROLES]
    cluster = assemble(faults, couplings, seed_ids)

    st.subheader("ベクトル種")
    st.table(_rows(faults, plain) or [{"id": "なし", "name": "", "distance": "", "role": ""}])

    st.subheader("交絡候補")
    st.table(_rows(faults, confounders) or [{"id": "なし", "name": "", "distance": "", "role": ""}])

    st.subheader("経路で追加したカード")
    path_rows = []
    for item in cluster:
        if item["reason"] != "path":
            continue
        path_rows.append({"id": item["id"], "name": faults[item["id"]]["name"], "reason": item["reason"]})
    st.table(path_rows or [{"id": "なし", "name": "", "reason": ""}])

    st.subheader("結合ノート")
    note_rows = []
    for item in cluster:
        if item["reason"] != "coupling":
            continue
        note_rows.append({"id": item["id"], "name": couplings[item["id"]]["name"], "text": couplings[item["id"]]["text"]})
    st.table(note_rows or [{"id": "なし", "name": "", "text": ""}])

    st.subheader("診断文")
    names = listed_models(host)
    generation = next((candidate for candidate in GENERATION_MODELS if model_present(names, candidate)), None)
    if generation is None:
        st.info("生成モデルが無いので診断文は作りません。")
        return
    system, user = render(query.strip(), cluster)
    with st.spinner(f"{generation} が診断文を書いています。"):
        st.markdown(generate(host, generation, system, user))


main()
