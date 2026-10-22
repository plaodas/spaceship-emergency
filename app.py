"""Streamlit view of the same diagnosis path as shipdiag.diagnose."""

import os

import streamlit as st

from shipdiag.diagnose import CHROMA_PATH, GENERATION_MODELS
from shipdiag.dialogue import append_reply
from shipdiag.gate import DATA, MODEL_FILE
from shipdiag.index import index_faults, persistent_client
from shipdiag.ollama import DEFAULT_HOST, embedder, generate, listed_models, model_present, ollama_ready
from shipdiag.prompt import render
from shipdiag.retrieve import SEED_LIMIT, assemble, clause_seeds
from shipdiag.validate import load_corpus, validate_corpus
from shipdiag.verdict import parse_verdict

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


def run_diagnosis(host, model, query):
    faults, couplings, embed, collection = prepare(host, model)
    hits = clause_seeds(query, embed, collection, limit=SEED_LIMIT)
    cluster = assemble(faults, couplings, [card_id for card_id, _distance in hits])
    names = listed_models(host)
    generation = next((candidate for candidate in GENERATION_MODELS if model_present(names, candidate)), None)
    diagnosis = None
    measurements = []
    if generation is not None:
        system, user = render(query, cluster["items"], cluster["mode"])
        diagnosis = generate(host, generation, system, user)
        verdict = parse_verdict(diagnosis)
        if verdict is not None:
            measurements = verdict["measurements"]
    return {
        "hits": hits,
        "items": cluster["items"],
        "mode": cluster["mode"],
        "diagnosis": diagnosis,
        "generation": generation,
        "measurements": measurements,
    }


def _start():
    st.session_state.query = st.session_state.draft.strip()
    st.session_state.do_run = True


def _accept_reply():
    reply = st.session_state.reply_input.strip()
    if not reply:
        return
    st.session_state.query = append_reply(st.session_state.query, reply)
    st.session_state.draft = st.session_state.query
    st.session_state.reply_input = ""
    st.session_state.do_run = True


def _show(faults, couplings, result):
    hits = result["hits"]
    plain = [(card_id, distance) for card_id, distance in hits if faults[card_id]["role"] not in CONFOUNDER_ROLES]
    confounders = [(card_id, distance) for card_id, distance in hits if faults[card_id]["role"] in CONFOUNDER_ROLES]

    st.caption(f"経路: {result['mode']}")

    st.subheader("ベクトル種")
    st.table(_rows(faults, plain) or [{"id": "なし", "name": "", "distance": "", "role": ""}])

    st.subheader("交絡候補")
    st.table(_rows(faults, confounders) or [{"id": "なし", "name": "", "distance": "", "role": ""}])

    st.subheader("経路で追加したカード")
    path_rows = []
    for item in result["items"]:
        if item["reason"] != "path":
            continue
        path_rows.append({"id": item["id"], "name": faults[item["id"]]["name"], "reason": item["reason"]})
    st.table(path_rows or [{"id": "なし", "name": "", "reason": ""}])

    st.subheader("結合ノート")
    note_rows = []
    for item in result["items"]:
        if item["reason"] != "coupling":
            continue
        note_rows.append({"id": item["id"], "name": couplings[item["id"]]["name"], "text": couplings[item["id"]]["text"]})
    st.table(note_rows or [{"id": "なし", "name": "", "text": ""}])


def main():
    st.set_page_config(page_title="宇宙船故障診断")
    st.title("宇宙船故障診断")
    host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
    if not ollama_ready(host):
        st.error(f"Ollama が {host} で応答しません。")
        return
    model = MODEL_FILE.read_text(encoding="utf-8").strip()
    st.session_state.setdefault("query", "")
    st.session_state.setdefault("draft", "")
    st.session_state.setdefault("reply_input", "")
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("do_run", False)
    st.session_state.setdefault("warn", False)

    if st.session_state.do_run:
        st.session_state.do_run = False
        if st.session_state.query:
            st.session_state.result = run_diagnosis(host, model, st.session_state.query)
            st.session_state.warn = False
        else:
            st.session_state.result = None
            st.session_state.warn = True

    st.text_area("症状", height=120, key="draft")
    st.button("診断", type="primary", on_click=_start)
    if st.session_state.warn:
        st.warning("症状文を入れてください。")

    result = st.session_state.result
    if result is None:
        return

    faults, couplings, _embed, _collection = prepare(host, model)
    _show(faults, couplings, result)

    st.subheader("診断文")
    if result["generation"] is None:
        st.info("生成モデルが無いので診断文は作りません。")
        return
    st.markdown(result["diagnosis"] or "")
    if not result["measurements"]:
        return
    st.subheader("確認計測")
    st.write(result["measurements"][0])
    st.text_input("計測の結果", key="reply_input")
    st.button("返事を足す", on_click=_accept_reply)


main()
