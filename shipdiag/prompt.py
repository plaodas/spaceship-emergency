"""Diagnosis prompt. The context holds observations, not a written conclusion."""

SYSTEM = """あなたはアルケオン型探査艦の整備診断者です。渡された文書だけを根拠にします。
次の順で書きます。
1. 部分一致。どの文書がクエリのどの部分に対応するか。
2. 共有部品。分かれた観測を一つの時間窓へ載せる接続。
3. 報告に無い識別症状。識別症状にあって、クエリに無いもの。
4. 棄却。交絡を本命にしない理由。
5. 確認計測。
故障カードを2枚以上、結合ノートを1枚以上引用します。単一カードを診断にしません。
深刻度は、経路として同時に起きている故障の運用影響で決めます。"""


def render(query, cluster):
    """Return (system, user). User text lists evidence and does not add a conclusion."""
    blocks = [f"クエリ: {query}", ""]
    for item in cluster:
        lines = [
            f"id: {item['id']}",
            f"採用理由: {item['reason']}",
            f"本文: {item['body']}",
        ]
        if item["cause"]:
            lines.append(f"原因: {item['cause']}")
        if item["discriminators"]:
            lines.append("識別症状: " + "".join(item["discriminators"]))
        blocks.append("\n".join(lines))
        blocks.append("")
    return SYSTEM, "\n".join(blocks).strip()
