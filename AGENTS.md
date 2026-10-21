# AGENTS.md

アルケオン型探査艦の故障診断RAG。結論は故障カードにも結合ノートにも書かない。部分一致した複数文書を Retriever が束ね、生成時にだけ診断が生まれる。全文検索アプリにしない。

仕様の詳細は docs が正本である。このファイルは、実装中に破りやすい制約だけを置く。

## 読む順

カード、結合ノート、検索、プロンプトを変更する前に、対象の文書を読む。

1. [docs/01-technology.md](docs/01-technology.md) — 8系統、部品ID、固定した物理制約
2. [docs/02-card-rules.md](docs/02-card-rules.md) — スキーマ、配分、禁止事項、結合ノート24件
3. [docs/03-symptom-queries.md](docs/03-symptom-queries.md) — 症状50件と種別
4. [docs/04-retrieval.md](docs/04-retrieval.md) — Retriever と MVP
5. [docs/05-demo-diagnosis.md](docs/05-demo-diagnosis.md) — Q01 の予約本文と統合診断

## 固定スタック

- Python、Ollama、Chroma 永続化、Streamlit
- 埋め込みは `bge-m3`。Q01 で FLT-017 が上位8件に入らなければ `qwen3-embedding:4b` に替える
- 生成は `qwen3:8b`。VRAM が厳しければ `qwen3:4b`
- 依存は `ollama`、`chromadb`、`streamlit`
- Qdrant へは移さない

## データ制約

- [docs/01-technology.md](docs/01-technology.md) の4つの物理制約以外を足さない
- カードと結合ノートに、乗員語 `燃費` `ワープ` `エンジンルーム` `警告灯` `右側` `左側` を入れない。トークン `ワープ` をカードへ足して検索をごまかさない
- 1枚のカードに、ジャンプ復帰の時間窓と反物質消費の増加を同居させない
- `FLT-044` の trigger に `after_jump` を付けない。熱入力のあとは `after_heat_pulse`
- 結合ノートは部品の接続だけを書く。乗員症状の結論を書かない。類似検索の種にしない
- 予約ID `FLT-008` `FLT-017` `FLT-028` `FLT-044` `FLT-052` `FLT-061` `CPL-03` の本文は [docs/05-demo-diagnosis.md](docs/05-demo-diagnosis.md) を正とし、書き換えない

## 検索制約

- 故障カードの類似上位8件を種にする。1位を診断にしない
- `derived` は双方向に1ホップだけ辿る。種どうしを結ぶ経路を優先し、経路の先の下流はプロンプトに足さない
- 結合ノートは、`links` の部品が展開後の集合に2個以上含まれるときだけ足す
- 交絡カードは検索段階で捨てない。棄却は生成側が行う
- 生成の順は、部分一致、共有部品、報告に無い識別症状、棄却、確認計測
- `compose` では故障カードを2枚以上、結合ノートを1枚以上引用する。単一カードを診断にしない

## 実装順

4段階で進める。段階の途中で止め、類似検索だけを完成にしない。ベクトル検索とグラフ展開は段階3でセットで動かす。先に通すのは Q01 のデモ集合だけであり、予約本文は [docs/05-demo-diagnosis.md](docs/05-demo-diagnosis.md) を使う。

1. デモコーパスとバリデータ。Ollama も Chroma も使わない。予約6カードと `CPL-03` を本文のままデータにし、[docs/02-card-rules.md](docs/02-card-rules.md) の検査を通す。`FLT-044` の trigger は `after_heat_pulse`。100件、bridge 20件、残りの結合ノートは書かない。
2. 埋め込みの関門。デモの故障カードだけを `fault_cards` に入れる。`CPL-03` は類似検索の種にしない。`bge-m3` で Q01 を検索し、FLT-017 が上位8件に入らなければ `qwen3-embedding:4b` に替える。
3. Retriever と診断。UI は作らない。上位8件、双方向1ホップ、種どうしを結ぶ経路、部品が2個以上一致する結合ノート、診断プロンプトまでをスクリプトで出す。同じ小コーパスで全文検索のベースラインを一度取る。終わりは下の完了の目安。
4. 件数と画面。段階3のあとだけ進む。結合ノート24件、bridge 20件、残りを足して100件にし、関門を再実行する。その後 Streamlit でベクトル種とグラフ追加、引用付き診断、棄却カードを分ける。[docs/03-symptom-queries.md](docs/03-symptom-queries.md) の compose 約15件でクラスタ再現を見る。

採点はクラスタの再現で行う。診断文の文字列一致では採点しない。

## 完了の目安

Q01「最近ワープ直後だけ機体の右側が熱くなる。燃費も悪化した。」で、次を満たす。

- 拡張前の類似上位に `CPL-03` が無い
- 拡張後のクラスタに `CPL-03` がある
- プロンプトへ渡す文書は、FLT-017、FLT-044、FLT-028、CPL-03、および交絡の FLT-052、FLT-061、FLT-008
