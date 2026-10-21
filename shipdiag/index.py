"""Index the demo fault cards. Coupling notes are not included."""

import chromadb

from shipdiag.documents import fault_embed_text, fault_metadata

COLLECTION = "fault_cards"


def index_faults(faults, embed, client, model_name):
    """Replace fault_cards with exactly the given fault cards."""
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine", "embedding_model": model_name},
    )
    ids = sorted(faults)
    texts = [fault_embed_text(faults[card_id]) for card_id in ids]
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embed(texts),
        metadatas=[fault_metadata(faults[card_id]) for card_id in ids],
    )
    return collection


def search(collection, query_vector, k):
    """Return (id, distance) pairs, nearest first."""
    count = collection.count()
    if count == 0:
        return []
    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(k, count),
    )
    return list(zip(result["ids"][0], result["distances"][0]))


def persistent_client(path):
    return chromadb.PersistentClient(path=str(path))
