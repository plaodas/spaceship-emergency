"""Read the trailing cited/primary/rejected/measurements block. Prose is ignored."""

import re

_KEYS = ("cited", "primary", "rejected", "measurements")
_LINE = re.compile(r"^(cited|primary|rejected|measurements):\s*(.*)$")


def _ids(value):
    parts = []
    for raw in value.replace(",", " ").replace("、", " ").split():
        part = raw.strip(" ,、。")
        if part:
            parts.append(part)
    return parts


def parse_verdict(text):
    """Return the trailing four-line block, or None when it is missing."""
    if not text:
        return None
    found = {}
    for line in text.splitlines():
        match = _LINE.match(line.strip())
        if match:
            found[match.group(1)] = match.group(2).strip()
    if set(found) != set(_KEYS):
        return None
    measurement = found["measurements"]
    return {
        "cited": _ids(found["cited"]),
        "primary": _ids(found["primary"]),
        "rejected": _ids(found["rejected"]),
        "measurements": [measurement] if measurement else [],
    }


def verdict_issues(verdict, required, avoid):
    """Required ids must be cited. Avoid ids must not be primary."""
    if verdict is None:
        return ["採点行がありません"]
    issues = []
    missing = [doc_id for doc_id in required if doc_id not in verdict["cited"]]
    promoted = [doc_id for doc_id in avoid if doc_id in verdict["primary"]]
    if missing:
        issues.append("cited に無い: " + " ".join(missing))
    if promoted:
        issues.append("primary にある: " + " ".join(promoted))
    return issues
