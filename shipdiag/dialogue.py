"""Append a measurement reply to the symptom text. Cards stay unchanged."""


def append_reply(query, reply):
    """Place the reply after the symptom. An empty reply leaves the query as it is."""
    query = (query or "").strip()
    reply = (reply or "").strip()
    if not reply:
        return query
    if not query:
        return reply
    if query.endswith("。"):
        return query + reply
    return query + "。" + reply
