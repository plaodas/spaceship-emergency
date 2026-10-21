"""Build a diagnostic cluster from vector seeds, one graph hop, and coupling notes."""

SEED_LIMIT = 8


def assemble(faults, couplings, seed_ids):
    """Keep seeds and cards that sit between two seeds, then attach coupling notes."""
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
    components = set()
    for card_id in kept:
        components.update(faults[card_id]["components"])
    for note_id in sorted(couplings):
        links = set(couplings[note_id]["links"])
        if len(links & components) >= 2:
            items.append(_coupling_item(couplings[note_id]))
    return items


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
