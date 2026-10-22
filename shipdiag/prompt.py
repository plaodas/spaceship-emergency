"""Diagnosis prompt. The context holds observations, not a written conclusion."""

_ORDER = """あなたはアルケオン型探査艦の整備診断者です。渡された文書だけを根拠にします。
乗員語は整備語へ読み替えます。燃費は反物質の使用量、ワープはジャンプ復帰、エンジンルームは対消滅室周辺、警告灯は警報、右側は右舷、左側は左舷です。
次の順で書きます。
1. 部分一致。どの文書がクエリのどの部分に対応するか。
2. 共有部品。分かれた観測を一つの時間窓へ載せる接続。
3. 報告に無い識別症状。識別症状にあって、クエリに無いもの。
4. 棄却。交絡を本命にしない理由。
5. 確認計測。
深刻度は、経路として同時に起きている故障の運用影響で決めます。
クエリの一部に対応する文書は cited と primary に入れます。識別症状が報告と矛盾する文書だけを rejected に入れます。
回答の最後に、次の4行だけをこの順で書きます。4行より後には何も書きません。IDは空白で区切り、計測は1件の文にします。散文で触れた故障カードと結合ノートの ID は cited に書きます。
cited: 引用したID
primary: 本命にしたID
rejected: 棄却したID
measurements: 報告に無い確認計測"""

_MODE = {
    "compose": "故障カードを2枚以上、結合ノートを1枚以上引用します。単一カードを診断にしません。",
    "independent": "経路は分かれています。一つの時間窓へ束ねず、故障カードを併記します。結合ノートの引用は要りません。",
    "single": "結合は不要です。その旨を書いてから、故障カード1枚を主にしてよい。",
}


def system_prompt(mode):
    return _ORDER + "\n" + _MODE[mode]


SYSTEM = system_prompt("compose")


def render(query, cluster, mode="compose"):
    """Return (system, user). User text lists evidence and does not add a conclusion."""
    blocks = [f"クエリ: {query}", f"経路: {mode}", ""]
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
    return system_prompt(mode), "\n".join(blocks).strip()
