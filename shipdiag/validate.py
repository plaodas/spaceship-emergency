"""Card-rule checks. complete=True adds the finished-corpus quotas."""

from pathlib import Path

import yaml

from shipdiag.ontology import (
    COMPONENTS,
    CREW_WORDS,
    ROLE_QUOTAS,
    ROLES,
    SYSTEM_QUOTAS,
    SYSTEMS,
    TRIGGERS,
)

FAULT_FIELDS = (
    "id",
    "name",
    "symptoms",
    "cause",
    "severity",
    "systems",
    "derived",
    "components",
    "triggers",
    "role",
    "confusers",
    "discriminators",
)
COUPLING_FIELDS = ("id", "name", "links", "text")

# 「増え」だけを見ると「増えない」に一致する。予約の交絡カードはその否定形を使う。
INCREASE_MARKERS = ("増加", "増や", "増える")
TIME_MARKERS = ("通常空間へ戻", "90秒から180秒", "超光速")


def load_corpus(data_dir):
    """Load fault cards and coupling notes keyed by filename stem."""
    root = Path(data_dir)
    return _load_docs(root / "faults"), _load_docs(root / "couplings")


def validate_corpus(faults, couplings, complete=False):
    """Return human-readable issues. An empty list means the corpus passed."""
    issues = []
    issues.extend(_validate_faults(faults))
    issues.extend(_validate_couplings(couplings))
    issues.extend(_validate_cross_document(faults, couplings))
    if complete:
        issues.extend(_validate_complete(faults))
    return issues


def _load_docs(directory):
    docs = {}
    if not directory.is_dir():
        return docs
    for path in sorted(directory.glob("*.yaml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            docs[path.stem] = {"id": path.stem}
            continue
        docs[path.stem] = _strip(loaded)
    return docs


def _strip(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_strip(item) for item in value]
    if isinstance(value, dict):
        return {key: _strip(item) for key, item in value.items()}
    return value


def _validate_faults(faults):
    issues = []
    for key, card in faults.items():
        label = str(card.get("id") or key)
        missing = [field for field in FAULT_FIELDS if field not in card]
        if missing:
            issues.append(f"{label}: 必須フィールドが無い ({', '.join(missing)})")
            continue
        if card["id"] != key:
            issues.append(f"{label}: ファイル名と id が一致しない")
        if not isinstance(card["severity"], int) or not 1 <= card["severity"] <= 5:
            issues.append(f"{label}: severity は 1 から 5 の整数")
        if card["systems"] not in SYSTEMS:
            issues.append(f"{label}: 未知の系統 {card['systems']!r}")
        _check_id_list(issues, label, "components", card["components"], COMPONENTS, 1, 3)
        _check_id_list(issues, label, "triggers", card["triggers"], TRIGGERS, 1, None)
        if card["role"] not in ROLES:
            issues.append(f"{label}: 未知の role {card['role']!r}")
        _check_string_list(issues, label, "derived", card["derived"])
        _check_string_list(issues, label, "confusers", card["confusers"])
        _check_string_list(issues, label, "discriminators", card["discriminators"])
        if card["id"] in card.get("derived", []):
            issues.append(f"{label}: derived が自分自身を指している")
        symptoms = card["symptoms"] if isinstance(card["symptoms"], str) else ""
        cause = card["cause"] if isinstance(card["cause"], str) else ""
        if not 80 <= len(symptoms) <= 220:
            issues.append(f"{label}: symptoms は 80〜220 字 (今は {len(symptoms)} 字)")
        prose = symptoms + cause
        if _has_time_window(prose) and _has_consumption_increase(prose):
            issues.append(f"{label}: ジャンプ復帰の時間窓と反物質消費の増加が同居している")
        if _has_all_four_facts(prose):
            issues.append(f"{label}: 時間窓・右舷外板温度・消費増加・弁の合流が同一本文にある")
        if label == "FLT-044" and "after_jump" in card.get("triggers", []):
            issues.append("FLT-044: triggers に after_jump がある")
        crew_fields = [card["name"], symptoms, cause]
        if isinstance(card["discriminators"], list):
            crew_fields.extend(item for item in card["discriminators"] if isinstance(item, str))
        _check_crew_words(issues, label, crew_fields)
    return issues


def _validate_couplings(couplings):
    issues = []
    for key, note in couplings.items():
        label = str(note.get("id") or key)
        missing = [field for field in COUPLING_FIELDS if field not in note]
        if missing:
            issues.append(f"{label}: 必須フィールドが無い ({', '.join(missing)})")
            continue
        if note["id"] != key:
            issues.append(f"{label}: ファイル名と id が一致しない")
        _check_id_list(issues, label, "links", note["links"], COMPONENTS, 2, 4)
        text = note["text"] if isinstance(note["text"], str) else ""
        if not 80 <= len(text) <= 220:
            issues.append(f"{label}: text は 80〜220 字 (今は {len(text)} 字)")
        if _has_all_four_facts(text):
            issues.append(f"{label}: 時間窓・右舷外板温度・消費増加・弁の合流が同一本文にある")
        _check_crew_words(issues, label, [note["name"], text])
    return issues


def _validate_cross_document(faults, couplings):
    issues = []
    known = set(faults)
    for key, card in faults.items():
        label = str(card.get("id") or key)
        for field in ("derived", "confusers"):
            values = card.get(field)
            if not isinstance(values, list):
                continue
            for target in values:
                if not isinstance(target, str):
                    continue
                if target == label:
                    continue
                if target not in known:
                    issues.append(f"{label}: {field} の {target} がコーパスに無い")
    return issues


def _validate_complete(faults):
    issues = []
    incoming = {key: 0 for key in faults}
    for key, card in faults.items():
        label = str(card.get("id") or key)
        derived = card.get("derived")
        if not isinstance(derived, list) or len(derived) < 1:
            issues.append(f"{label}: 完成コーパスでは derived が 1 件以上必要")
        elif isinstance(derived, list):
            for target in derived:
                if target in incoming:
                    incoming[target] += 1
    for key, card in faults.items():
        derived = card.get("derived")
        out_degree = len(derived) if isinstance(derived, list) else 0
        if incoming.get(key, 0) == 0 and out_degree == 0:
            issues.append(f"{key}: 孤立ノード")
    role_counts = {role: 0 for role in ROLE_QUOTAS}
    system_counts = {system: 0 for system in SYSTEM_QUOTAS}
    for card in faults.values():
        role = card.get("role")
        system = card.get("systems")
        if role in role_counts:
            role_counts[role] += 1
        if system in system_counts:
            system_counts[system] += 1
    for role, expected in ROLE_QUOTAS.items():
        actual = role_counts[role]
        if actual != expected:
            issues.append(f"role {role} は {actual} 件で、配分 {expected} 件ではない")
    for system, expected in SYSTEM_QUOTAS.items():
        actual = system_counts[system]
        if actual != expected:
            issues.append(f"系統 {system} は {actual} 件で、配分 {expected} 件ではない")
    return issues


def _check_id_list(issues, label, field, value, allowed, minimum, maximum):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        issues.append(f"{label}: {field} は文字列のリスト")
        return
    if len(value) < minimum or (maximum is not None and len(value) > maximum):
        span = f"{minimum}" if maximum is None else f"{minimum}〜{maximum}"
        issues.append(f"{label}: {field} は {span} 個")
    unknown = [item for item in value if item not in allowed]
    if unknown:
        issues.append(f"{label}: {field} に未知の ID {unknown}")


def _check_string_list(issues, label, field, value):
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        issues.append(f"{label}: {field} は文字列のリスト")


def _check_crew_words(issues, label, texts):
    for text in texts:
        for word in CREW_WORDS:
            if word in text:
                issues.append(f"{label}: 乗員語「{word}」がある")
                return


def _has_time_window(text):
    return any(marker in text for marker in TIME_MARKERS)


def _has_consumption_increase(text):
    has_amount = "使用量" in text or "流量" in text
    has_increase = any(marker in text for marker in INCREASE_MARKERS)
    return "反物質" in text and has_amount and has_increase


def _has_all_four_facts(text):
    has_hull = "右舷外板" in text and "温度" in text
    has_join = "合流" in text or "同一弁体" in text
    return (
        _has_time_window(text)
        and has_hull
        and _has_consumption_increase(text)
        and has_join
    )
