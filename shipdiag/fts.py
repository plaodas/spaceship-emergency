"""BM25 over Japanese script runs. Okurigana stays attached, so stems are not cut."""

import math
import re

# 送り仮名は漢字に付けたままにする。ひらがなだけ（助詞）はトークンにしない。
_TOKEN = re.compile(r"[一-鿿]+[ぁ-ん]*|[ァ-ヶー]+")
_K1 = 1.5
_B = 0.75


def tokenize(text):
    return _TOKEN.findall(text)


def score_corpus(documents, query):
    """Score (id, text) pairs against the query. Higher is closer."""
    tokenized = [(doc_id, tokenize(text)) for doc_id, text in documents]
    query_terms = tokenize(query)
    scores = {doc_id: 0.0 for doc_id, _tokens in tokenized}
    if not query_terms or not tokenized:
        return scores
    doc_count = len(tokenized)
    lengths = [len(tokens) for _doc_id, tokens in tokenized]
    average = sum(lengths) / doc_count
    if average == 0:
        return scores
    document_frequency = {}
    for _doc_id, tokens in tokenized:
        for term in set(tokens):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    for index, (doc_id, tokens) in enumerate(tokenized):
        counts = {}
        for term in tokens:
            counts[term] = counts.get(term, 0) + 1
        length = lengths[index]
        for term in query_terms:
            frequency = counts.get(term, 0)
            if frequency == 0:
                continue
            df = document_frequency.get(term, 0)
            idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1)
            denom = frequency + _K1 * (1 - _B + _B * length / average)
            scores[doc_id] += idf * (frequency * (_K1 + 1)) / denom
    return scores


def document_text(card=None, note=None):
    if card is not None:
        return "\n".join([card["name"], card["symptoms"], card["cause"]])
    return "\n".join([note["name"], note["text"]])
