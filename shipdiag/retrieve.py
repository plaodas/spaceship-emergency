"""Build a diagnostic cluster from clause seeds, one graph hop, and coupling notes."""

from shipdiag.index import search

SEED_LIMIT = 8


def split_clauses(query):
    """Split on '。'. Blank pieces are dropped."""
    return [part.strip() for part in query.split("。") if part.strip()]


def merge_hits(groups, limit=SEED_LIMIT):
    """Keep the nearer distance for each card, then the nearest `limit` cards."""
    best = {}
    for hits in groups:
        for card_id, distance in hits:
            current = best.get(card_id)
            if current is None or distance < current:
                best[card_id] = distance
    ranked = sorted(best.items(), key=lambda item: (item[1], item[0]))
    return ranked[:limit]


def seeds_for(query, embed, search_one, limit=SEED_LIMIT):
    """Search each sentence. A single sentence embeds the raw query once."""
    clauses = split_clauses(query)
    if len(clauses) <= 1:
        return list(search_one(embed([query])[0]))[:limit]
    vectors = embed(clauses)
    return merge_hits([search_one(vector) for vector in vectors], limit)


def clause_seeds(query, embed, collection, limit=SEED_LIMIT):
    """Same seed path for the gate, diagnosis, evaluation, and the UI."""
    return seeds_for(query, embed, lambda vector: search(collection, vector, limit), limit)


def assemble(faults, couplings, seed_ids):
    """Keep seeds and cards between two seeds, then couplings inside one component.

    Returns {"items", "mode"}. mode is compose, independent, or single.
    """
    seeds = _unique_known(seed_ids, faults)[:SEED_LIMIT]
    adjacency = _adjacency(faults)
    kept = list(seeds)
    seed_set = set(seeds)
    neighbors = set()
    for seed in seeds:
        neighbors.update(adjacency[seed])
    for node in sorted(neighbors - seed_set):
        if _bridges_two_seeds(node, adjacency, seed_set):
            kept.append(node)
    items = [_fault_item(faults[card_id], "seed" if card_id in seed_set else "path") for card_id in kept]
    card_groups = _groups(kept, adjacency)
    part_groups = []
    kept_parts = set()
    for cards in card_groups:
        parts = set()
        for card_id in cards:
            parts.update(faults[card_id]["components"])
        part_groups.append(parts)
        kept_parts.update(parts)
    attached = []
    for note_id in sorted(couplings):
        links = set(couplings[note_id]["links"])
        in_one_component = any(len(links & parts) >= 2 for parts in part_groups)
        ends_present = len(links) >= 2 and links <= kept_parts
        if in_one_component or ends_present:
            attached.append(note_id)
            items.append(_coupling_item(couplings[note_id]))
    if attached:
        mode = "compose"
    elif len(card_groups) >= 2:
        mode = "independent"
    else:
        mode = "single"
    return {"items": items, "mode": mode}


def _groups(kept, adjacency):
    """Component sets of kept cards. Each value is the part ids in that component."""
    remaining = set(kept)
    groups = []
    for start in kept:
        if start not in remaining:
            continue
        stack = [start]
        cards = []
        while stack:
            node = stack.pop()
            if node not in remaining:
                continue
            remaining.remove(node)
            cards.append(node)
            for neighbor in adjacency[node]:
                if neighbor in remaining:
                    stack.append(neighbor)
        groups.append(cards)
    return groups


def _unique_known(seed_ids, faults):
    seen = set()
    ordered = []
    for card_id in seed_ids:
        if card_id in faults and card_id not in seen:
            seen.add(card_id)
            ordered.append(card_id)
    return ordered


def _adjacency(faults):
    adjacency = {card_id: set() for card_id in faults}
    for card_id, card in faults.items():
        for target in card.get("derived") or []:
            if target not in adjacency:
                continue
            adjacency[card_id].add(target)
            adjacency[target].add(card_id)
    return adjacency


def _bridges_two_seeds(node, adjacency, seeds):
    """True when two seeds can meet only by passing through this node."""
    branches = []
    for neighbor in adjacency[node]:
        found = _seeds_from(neighbor, adjacency, blocked={node}, seeds=seeds)
        if found:
            branches.append(found)
    if len(branches) < 2:
        return False
    reached = set()
    for branch in branches:
        reached.update(branch)
    return len(reached) >= 2


def _seeds_from(start, adjacency, blocked, seeds):
    found = set()
    stack = [start]
    seen = set(blocked)
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in seeds:
            found.add(current)
        stack.extend(adjacency[current])
    return found


def _fault_item(card, reason):
    return {
        "id": card["id"],
        "reason": reason,
        "body": card["symptoms"],
        "cause": card["cause"],
        "discriminators": list(card["discriminators"]),
    }


def _coupling_item(note):
    return {
        "id": note["id"],
        "reason": "coupling",
        "body": note["text"],
        "cause": "",
        "discriminators": [],
    }
