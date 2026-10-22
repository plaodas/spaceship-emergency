"""Write the phase-4 corpus around the reserved demo cards.

Reserved symptom and cause text is left untouched. Only derived edges on
FLT-008, FLT-028, FLT-052, and FLT-061 are updated so the finished graph
has no empty derived list. CPL-03 is not rewritten.
"""

from pathlib import Path

from shipdiag.ontology import COMPONENT_NAMES, SYSTEM_QUOTAS
from shipdiag.validate import load_corpus, validate_corpus

ROOT = Path(__file__).resolve().parents[1]
FAULTS = ROOT / "data" / "faults"
COUPLINGS = ROOT / "data" / "couplings"

RESERVED = {"FLT-008", "FLT-017", "FLT-028", "FLT-044", "FLT-052", "FLT-061"}
PAIRS = {
    "FLT-008": ["FLT-009"],
    "FLT-009": ["FLT-008"],
    "FLT-017": ["FLT-044"],
    "FLT-044": ["FLT-028"],
    "FLT-028": ["FLT-073"],
    "FLT-052": ["FLT-053"],
    "FLT-053": ["FLT-052"],
    "FLT-061": ["FLT-062"],
    "FLT-062": ["FLT-061"],
    "FLT-073": ["FLT-074"],
    "FLT-074": ["FLT-073"],
}

PARTS = {
    "annihilation": [
        "antimatter_bottle",
        "port_injector",
        "starboard_injector",
        "annihilation_chamber",
        "annihilation_jacket",
        "photon_nozzle",
    ],
    "fold": ["starboard_fold_coil", "port_fold_coil", "mass_shadow_compensator"],
    "dark_thermal": [
        "dark_thermal_bus",
        "starboard_dark_valve",
        "port_dark_valve",
        "dark_matter_reservoir",
        "thermal_check_valve",
    ],
    "gravity": ["starboard_damper", "port_damper", "gravity_deck"],
    "comms": ["entanglement_bank", "phase_lock_array", "decoherence_shield"],
    "power": ["zpe_bus", "starboard_power_leg"],
    "shield": ["starboard_shield_emitter", "port_shield_emitter"],
    "life_support": ["starboard_habitat_duct", "port_habitat_duct", "atmosphere_loop"],
    "sensors": ["hull_temp_sensor", "consumption_sensor", "phase_sensor"],
    "hull": ["starboard_hull", "port_hull", "hull_integrity_field"],
}

WHEN = {
    "steady": "定常運転",
    "during_burn": "対消滅の燃焼",
    "high_power": "高出力の給電",
    "shield_on": "シールド展開",
    "maneuver": "姿勢変更",
    "comms_active": "通信ロックの維持",
    "during_jump": "折畳みの途中",
    "after_heat_pulse": "熱パルスのあと",
}
FILLER_TRIGGERS = list(WHEN)
MODES = {
    "local": ["応答遅れ", "脈動", "開度不足", "位相のずれ", "熱の滞留", "同期外れ", "密封の漏れ", "保持力の低下"],
    "bridge": ["境界での滞り", "共有点の飽和", "受け渡しの遅れ", "境界の脈動"],
    "confounder": ["見かけの偏差", "別原因の重なり", "同時に見える揺れ", "時刻の一致"],
    "sensor_lie": ["指示の偏り", "校正のずれ", "表示だけの変化", "基準点の移動"],
}


def fit(text):
    extra = "同じ偏差は当該部品の記録に残る。"
    while len(text) < 80:
        text += extra
    if not 80 <= len(text) <= 220:
        raise ValueError(f"length {len(text)}: {text}")
    return text


def dump_card(card):
    lines = [
        f"id: {card['id']}",
        f"name: {card['name']}",
        f"symptoms: {card['symptoms']}",
        f"cause: {card['cause']}",
        f"severity: {card['severity']}",
        f"systems: {card['systems']}",
        "derived:",
    ]
    for target in card["derived"]:
        lines.append(f"  - {target}")
    lines.append("components:")
    for component in card["components"]:
        lines.append(f"  - {component}")
    lines.append("triggers:")
    for trigger in card["triggers"]:
        lines.append(f"  - {trigger}")
    lines.append(f"role: {card['role']}")
    lines.append("confusers: []")
    lines.append("discriminators:")
    for item in card["discriminators"]:
        lines.append(f"  - {item}")
    return "\n".join(lines) + "\n"


def dump_note(note):
    lines = [
        f"id: {note['id']}",
        f"name: {note['name']}",
        "links:",
    ]
    for link in note["links"]:
        lines.append(f"  - {link}")
    lines.append(f"text: {note['text']}")
    return "\n".join(lines) + "\n"


def replace_derived(path, targets):
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    output = []
    index = 0
    found = False
    while index < len(lines):
        if lines[index].startswith("derived:"):
            found = True
            output.append("derived:\n")
            for target in targets:
                output.append(f"  - {target}\n")
            index += 1
            while index < len(lines) and lines[index].startswith("  - "):
                index += 1
            continue
        output.append(lines[index])
        index += 1
    if not found:
        raise RuntimeError(path)
    path.write_text("".join(output), encoding="utf-8")


def pinned_cards():
    rows = [
        ("FLT-009", "右舷給電レグの接触抵抗", "power", "local", ["starboard_power_leg"], ["high_power"], 2,
         "右舷給電レグの接続部に接触抵抗が出て、レグの末端電圧が指令より低くなる。低さは電流が大きいときに広がり、電流を落とすと末端電圧は指令へ戻る。",
         "接続部の抵抗が、レグ末端の電圧を指令から引き離す。",
         "電流を落とすと末端電圧は指令へ戻る。"),
        ("FLT-010", "零点母線の全舷低下", "power", "local", ["zpe_bus"], ["steady"], 3,
         "零点母線の電圧が全舷で低下し、照明の出力が一緒に落ちる。落ち方は左右の外板を区別せず、温度の上がり方も特定の舷に寄らない。低下は定常の給電のあいだ続く。",
         "母線の電圧低下が、全舷の照明と制御電源を同時に弱める。",
         "特定の舷だけが暗い、という偏りは出ない。"),
        ("FLT-013", "右舷弁制御のレグ依存", "power", "bridge", ["starboard_dark_valve"], ["steady"], 3,
         "右舷暗黒熱弁の制御電力が、右舷給電レグの電圧に合わせて落ちる。弁の機械的な固着は見られず、レグの電圧が戻ると制御も戻る。熱の滞りはこのカードでは述べない。",
         "弁の制御電源が給電レグの電圧に従う。",
         "レグの電圧が基準なら、弁の制御電力も基準である。"),
        ("FLT-018", "質量影による折畳み位相の乱れ", "fold", "local", ["starboard_fold_coil"], ["during_jump"], 2,
         "右舷折畳みコイルの駆動が、質量影の勾配に合わせて位相を乱す。乱れのあいだコイルの温度は基準のままである。影が弱いときは位相も基準へ戻る。",
         "質量影の勾配が、コイル駆動の位相基準を揺らす。",
         "コイルの温度指示は基準のままである。"),
        ("FLT-019", "折畳み復帰後の駆動位相ずれ", "fold", "local", ["starboard_fold_coil"], ["after_jump"], 2,
         "右舷折畳みコイルの駆動位相が、折畳みから戻った短い時間だけずれる。ずれているあいだコイルの温度指示は基準のままである。位相は駆動が静まると基準へ戻る。",
         "復帰直後の残渣位相が、コイルの駆動基準をずらす。",
         "温度指示は基準のままで、位相だけがずれる。"),
        ("FLT-020", "強補償時の折畳み位相乱れ", "fold", "local", ["starboard_fold_coil"], ["high_power"], 3,
         "質量影補償を強くしたとき、右舷折畳みコイルの駆動位相が補償器の負荷に合わせて乱れる。乱れは温度の指示には出ない。補償を弱めると位相は基準へ戻る。",
         "補償器の負荷が、コイル駆動の位相基準を動かす。",
         "温度指示は補償の強さでは変わらない。"),
        ("FLT-029", "両外套の定常加熱", "annihilation", "local", ["annihilation_jacket"], ["steady"], 2,
         "対消滅室の外套が、定常の燃焼で左右とも熱を持つ。熱は特定の舷に寄らず、折畳みの時刻にも揃わない。燃焼を止めると両方の指示が一緒に下がる。",
         "燃焼中の廃熱が、両外套へ同じように残る。",
         "特定の舷だけが熱い、という差は出ない。"),
        ("FLT-030", "対消滅室の光子漏洩", "annihilation", "local", ["annihilation_chamber"], ["during_burn"], 3,
         "対消滅室が燃焼しているあいだ、室から漏れる高エネルギー光子が増える。光子は室の外へ出て、燃焼を止めると元の量へ戻る。漏れの記録は室の外側の入射計に残る。",
         "燃焼中の室壁から、高エネルギー光子が外へ漏れる。",
         "燃焼を止めると漏洩は止まる。"),
        ("FLT-032", "指令不変の噴射増量", "annihilation", "local", ["starboard_injector"], ["steady"], 3,
         "右舷噴射格子の供給が、推力の指令を変えずに増える。増加は反物質の使用量の記録に残り、外板の温度差には出ない。供給は指令を戻すと基準へ戻る。",
         "格子の制御が、指令より多い供給を続ける。",
         "外板の左右の温度差は増えない。"),
        ("FLT-045", "外套熱のバス受領", "dark_thermal", "local", ["dark_thermal_bus"], ["steady"], 2,
         "暗黒熱バスが外套から戻る熱を定常的に受け取っている。受け取りは左右の外板を区別しない。燃焼を止めると、バス入口の温度も外套と一緒に下がる。",
         "外套の廃熱が、バスの入口へ定常的に入る。",
         "受け取りは特定の舷の外板に寄らない。"),
        ("FLT-046", "貯槽残量の低下", "dark_thermal", "local", ["dark_matter_reservoir"], ["steady"], 2,
         "ダークマター貯槽の空きが減り、残量計の指示が下がる。空きの減少は貯槽の残量計に出る。熱を消す経路はこの貯槽の外にはない。",
         "貯槽に残る空きが、受け入れの余地を狭める。",
         "残量計の低下は貯槽側の記録に留まる。"),
        ("FLT-047", "貯槽空きに従うバス余力", "dark_thermal", "bridge", ["dark_thermal_bus"], ["after_heat_pulse"], 3,
         "暗黒熱バスが新たに受け取れる余力が、貯槽の空きに従って落ちる。余力が落ちても、特定の舷の外板だけが熱源になるわけではない。空きが戻ると受け取りの余力も戻る。",
         "バスの受け入れ上限が、貯槽の空きに従う。",
         "余力の低下は特定の舷の熱源を指さない。"),
        ("FLT-048", "コイル残熱のバス入口", "dark_thermal", "local", ["dark_thermal_bus"], ["after_jump"], 2,
         "折畳みから戻った短い時間、暗黒熱バスの入口温度がコイル残熱の流入で上がる。上がりはバス入口の記録に留まり、噴射格子の供給量は基準のままである。流入が終わると入口温度は戻る。",
         "コイルの残熱が、バス入口へ短い時間だけ流入する。",
         "噴射格子の供給量は基準のままである。"),
        ("FLT-053", "右舷エミッタの駆動余裕不足", "shield", "local", ["starboard_shield_emitter"], ["shield_on"], 2,
         "右舷シールドエミッタの駆動余裕が減り、同じ展開指令でも電界が基準より弱い。弱さは展開中だけ観測され、畳むと駆動電流は基準へ戻る。外板の温度はこの余裕の記録には出ない。",
         "駆動余裕の不足が、展開中の電界を基準から落とす。",
         "外板の温度はこの記録には出ない。"),
        ("FLT-054", "展開中のエミッタ入射熱", "shield", "local", ["starboard_shield_emitter"], ["shield_on"], 3,
         "右舷シールドエミッタが展開中に粒子を受け、入射熱で外板の温度指示が上がる。指示の変化は展開しているあいだに限られ、折畳みの時刻には揃わない。エミッタを畳むと指示は元の勾配へ戻る。",
         "展開中の粒子入射が、外板の温度指示を上げる。",
         "折畳みの時刻には揃わない。"),
        ("FLT-062", "右舷ダンパーの保持力低下", "gravity", "local", ["starboard_damper"], ["maneuver"], 2,
         "右舷慣性ダンパーの保持力が指令より小さく、機動のあとで加速度の残りが消えるまでが長い。残りはダンパーの位相計に出る。外板の温度とは別の記録である。",
         "保持力の不足が、機動後の加速度を残す。",
         "外板の温度とは別の記録である。"),
        ("FLT-063", "折畳み直前の甲板荷重", "gravity", "local", ["mass_shadow_compensator"], ["during_jump"], 3,
         "質量影補償器が折畳みへ入る直前に負荷を上げ、擬似重力甲板の指示が重くなる。重さは温度の変化を伴わない。補償を戻すと甲板の指示も基準へ戻る。負荷の記録は補償器に残る。",
         "折畳み直前の補償負荷が、甲板の加速度基準を上げる。",
         "温度の変化は伴わない。"),
        ("FLT-065", "強補償時の質量影負荷", "gravity", "local", ["mass_shadow_compensator"], ["high_power"], 3,
         "質量影補償を強くすると、補償器の負荷が上がり、折畳み位相の基準が同じ負荷を参照して乱れる。乱れは温度の指示には出ない。補償を弱めると負荷は下がる。",
         "強い補償が、補償器と折畳み位相の共通基準を動かす。",
         "温度指示は補償の強さでは変わらない。"),
        ("FLT-073", "光子ノズルの流量偏り", "annihilation", "local", ["photon_nozzle"], ["during_burn"], 2,
         "光子ノズルの出口で運動量が一方向へ偏る。偏りは噴射が続いているあいだ残り、ノズルを止めると消える。偏りは折畳みの時刻には揃わず、外板の温度指示とも別の記録に残る。",
         "上流の供給が偏ったあとで、ノズル内の流れが片側へ寄る。",
         "外板の温度指示とは別の記録に残る。"),
        ("FLT-074", "光子ノズルの片側摩耗", "annihilation", "local", ["photon_nozzle"], ["during_burn"], 2,
         "光子ノズルの片側内壁が痩せ、同じ指令でも出口の向きがわずかにずれる。ずれは燃焼のあいだ蓄積し、停止するとそれ以上は進まない。外板の温度とは別の監視点に出る。",
         "偏った流れが、内壁の片側だけを削る。",
         "外板の温度とは別の監視点に出る。"),
        ("FLT-081", "燃焼中の遮蔽入射", "comms", "local", ["decoherence_shield"], ["during_burn"], 3,
         "デコヒーレンス遮蔽の内側で位相雑音が上がり、通信ロックが燃焼のあいだだけ落ちる。燃焼を止めるとロックは戻る。雑音の記録は遮蔽の入射計に残る。",
         "遮蔽への入射が、燃焼中の位相雑音を上げる。",
         "燃焼を止めると通信ロックは戻る。"),
        ("FLT-082", "復帰直後の復号遅れ", "comms", "local", ["decoherence_shield"], ["after_jump"], 2,
         "デコヒーレンス遮蔽の復号タイミングが、折畳みから戻った短い時間だけ遅れる。遅延のあいだ温度の指示は変わらない。位相が静まるとロックは戻る。遅れは遮蔽側の記録に残る。",
         "復帰直後の残渣位相が、遮蔽の復号タイミングをずらす。",
         "温度の指示は変わらない。"),
        ("FLT-085", "強補償時の位相ロック外れ", "comms", "local", ["decoherence_shield"], ["high_power"], 3,
         "デコヒーレンス遮蔽の基準位相が、強い質量影補償のあいだ外れる。外れは補償を強くしているときに再現し、温度の指示は変わらない。補償を弱めると位相は戻る。",
         "補償に伴う位相の乱れが、遮蔽の基準を外す。",
         "温度指示は変わらない。"),
        ("FLT-090", "右舷ダクトの空気滞り", "life_support", "local", ["starboard_habitat_duct"], ["steady"], 2,
         "右舷居住区ダクトの空気が滞り、居住区のその舷だけが蒸し暑くなる。滞りのあいだ船体の外板の温度は基準のままである。循環を戻すと空気の温度も基準へ戻る。",
         "ダクト内の流れが滞り、居住区側の空気に熱が残る。",
         "外板の温度は基準のままである。"),
        ("FLT-096", "外板温度が基準のまま", "hull", "local", ["starboard_hull"], ["steady"], 1,
         "右舷外板の構造温度は基準のままで、居住区側の暑さとは別の値を示す。外板の監視点はダクト内の空気を測っていない。構造温度は定常の範囲に留まる。",
         "外板の構造温度の経路に、居住区の空気は入っていない。",
         "ダクト内の空気とは別の値を示す。"),
    ]
    cards = []
    for card_id, name, system, role, components, triggers, severity, symptoms, cause, disc in rows:
        cards.append(
            {
                "id": card_id,
                "name": name,
                "symptoms": fit(symptoms),
                "cause": cause,
                "severity": severity,
                "systems": system,
                "derived": PAIRS.get(card_id, []),
                "components": components,
                "triggers": triggers,
                "role": role,
                "discriminators": [disc],
            }
        )
    return cards


def notes():
    rows = [
        ("CPL-01", "右舷コイル残熱の出口", ["starboard_fold_coil", "dark_thermal_bus"],
         "右舷折畳みコイルが折畳みのあと残す熱の正規の出口は、暗黒熱バスだけである。バス以外の配管へはこの残熱を流さず、コイル側の熱はバスが受け取った分だけ下がる。"),
        ("CPL-02", "右舷ジャケット廃熱の出口", ["annihilation_jacket", "dark_thermal_bus"],
         "対消滅室右舷ジャケットが吸収した廃熱の正規の出口は、暗黒熱バスだけである。ジャケットからバス以外へ熱を捨てる経路はなく、バスが受け取るまでジャケット側の温度は下がらない。"),
        ("CPL-04", "左舷弁の回路", ["port_fold_coil", "port_dark_valve"],
         "左舷暗黒熱弁は左舷トリムコイル側の回路であり、右舷ジャケットの帰路を通さない。左舷の熱はこの弁から左舷側の配管へ進み、右舷の弁とは合流しない。"),
        ("CPL-05", "左右の弁の分離", ["starboard_dark_valve", "port_dark_valve"],
         "右舷暗黒熱弁と左舷暗黒熱弁は相互に接続しない。一方の弁の開度が変わっても、もう一方の弁の開度は変わらない。左右の熱回路は弁の手前で分かれたままである。"),
        ("CPL-06", "貯槽逆止弁", ["thermal_check_valve", "dark_matter_reservoir"],
         "逆止弁はダークマター貯槽から暗黒熱バスへの逆流を止める。貯槽側の圧力がバスより高くても、逆止弁が閉じているあいだ熱の流れはバスから貯槽へ戻らない。"),
        ("CPL-07", "貯槽残量とバス上限", ["dark_matter_reservoir", "dark_thermal_bus"],
         "ダークマター貯槽の残量が、暗黒熱バスが新たに受け取れる熱量の上限になる。残量が減るとバスが受け入れられる熱も減り、残量が戻ると受け入れの上限も戻る。貯槽は熱を消す部品ではない。"),
        ("CPL-08", "大気循環の廃熱入口", ["atmosphere_loop", "dark_thermal_bus"],
         "大気循環の廃熱は暗黒熱バスへ入る。居住区側の熱交換器から出た熱はこの入口を通り、バス以外の排出先へは分岐しない。循環が止まると、この入口からバスへ入る熱も止まる。"),
        ("CPL-09", "シールド廃熱の入口", ["starboard_shield_emitter", "dark_thermal_bus"],
         "右舷シールドエミッタの廃熱は暗黒熱バスへ入る。エミッタが展開して熱を出しているあいだ、その廃熱はこの入口からバスへ進む。エミッタを畳むと、この入口からの熱は止まる。"),
        ("CPL-10", "質量影補償器の共有", ["mass_shadow_compensator", "starboard_fold_coil", "gravity_deck"],
         "質量影補償器は折畳み航法と擬似重力甲板で共有する。補償器の負荷が変わると、右舷折畳みコイルの駆動と甲板の加速度基準が同じ負荷を参照する。熱の配管はこの共有に含まれない。"),
        ("CPL-11", "対消滅放射線と遮蔽", ["annihilation_chamber", "decoherence_shield"],
         "対消滅室の放射線はデコヒーレンス遮蔽に当たる。室が燃焼して放射線が出ると、遮蔽が受ける入射も増える。この入射は折畳みコイルの残熱配管を通らない。"),
        ("CPL-12", "残渣位相と遮蔽", ["starboard_fold_coil", "decoherence_shield"],
         "折畳みを終えた直後の残渣位相は、デコヒーレンス遮蔽に当たる。位相の残渣が遮蔽の基準を揺らし、コイルの温度そのものが遮蔽へ伝わるわけではない。残渣が消えると遮蔽への影響も消える。"),
        ("CPL-13", "冷却ポンプの電源", ["zpe_bus", "dark_thermal_bus"],
         "冷却ポンプの電源は零点母線である。母線の電圧が下がるとポンプへ届く電力も下がり、ポンプが送る暗黒熱バス側の流れが弱る。ポンプの電源は別系統の電池ではない。"),
        ("CPL-14", "位相ロックの電源", ["zpe_bus", "phase_lock_array"],
         "位相ロックアレイの電源は零点母線である。母線の電圧が下がるとロックを維持する電力も下がり、アレイの基準位相が保てなくなる。この電源は通信の信号経路そのものではない。"),
        ("CPL-15", "噴射格子制御の電源", ["zpe_bus", "starboard_injector"],
         "右舷噴射格子の制御電源は零点母線である。母線の電圧が下がると格子の制御が弱り、対消滅室へ送る量の指示が不安定になる。格子の制御電源は熱の配管ではない。"),
        ("CPL-16", "外板温度センサーの読取", ["hull_temp_sensor", "starboard_hull", "starboard_fold_coil"],
         "外板温度センサーは右舷外板を読む。折畳みから戻った直後の残渣位相が、このセンサーの指示をずらすことがある。指示のずれは外板の構造温度そのものの変化とは別である。"),
        ("CPL-17", "居住区と外板の分離", ["starboard_habitat_duct", "starboard_hull"],
         "右舷居住区ダクトの熱経路と、右舷外板の温度の経路は別である。ダクト内の空気が熱を持っても、外板の構造温度の経路へは接続していない。外板のセンサーはダクト内の空気を読まない。"),
        ("CPL-18", "粒子入射熱と外板", ["starboard_shield_emitter", "starboard_hull"],
         "右舷エミッタの粒子入射熱は右舷外板へ入る。エミッタが粒子を受けているあいだ、その熱は外板の温度を上げる向きに入る。この経路は折畳みコイルの残熱配管を通らない。同じ偏差は当該部品の記録に残る。"),
        ("CPL-19", "右舷ダンパーの力の経路", ["starboard_damper", "gravity_deck"],
         "右舷慣性ダンパーは乗員の体へ力を伝える経路であり、外板温度の経路ではない。ダンパーの位相がずれても外板の温度指示は変わらず、力の偏りはダンパー側の駆動に残る。"),
        ("CPL-20", "右舷給電レグの負荷", ["starboard_power_leg", "starboard_injector", "starboard_dark_valve"],
         "右舷給電レグは、右舷の噴射格子制御と冷却ポンプを同じレグで賄う。レグの電圧が下がると、噴射格子の制御と右舷暗黒熱弁へ向かう冷却側の電力が同時に弱る。原因はレグ側にある。"),
        ("CPL-21", "光子ノズルの推力配分", ["port_injector", "starboard_injector", "photon_nozzle"],
         "光子ノズルの推力バランスは、左舷噴射格子と右舷噴射格子の両方に依存する。片側の格子の出力だけが変わると、ノズル内の運動量が一方向へ偏る。ノズルは二つの格子の出力を一つの開口で受けている。"),
        ("CPL-22", "位相ロックともつれ対", ["phase_lock_array", "entanglement_bank"],
         "位相ロックアレイは、もつれ対バンクから対を引き出す。バンクの対が減るとロックが使える対も減り、ロックの維持が難しくなる。対の在庫はアレイの位相そのものとは別の量である。"),
        ("CPL-23", "甲板の加速度基準", ["gravity_deck", "mass_shadow_compensator"],
         "擬似重力甲板の加速度基準は質量影補償器である。補償器の基準が変わると、甲板が示す加速度も同じ基準に従う。この基準は外板の温度や熱の配管を参照しない。"),
        ("CPL-24", "消費センサーの読取", ["consumption_sensor", "starboard_injector"],
         "反物質消費センサーは右舷噴射格子の実流量を読む。センサーの指示だけがずれても、格子の実流量は指示どおりには変わらない。流量を決めるのは格子側の制御である。"),
    ]
    return [
        {"id": note_id, "name": name, "links": links, "text": fit(text)}
        for note_id, name, links, text in rows
    ]


def filler_cards(pinned):
    remaining = dict(SYSTEM_QUOTAS)
    for card in pinned:
        remaining[card["systems"]] -= 1
    for card_id in RESERVED:
        system = {
            "FLT-008": "power",
            "FLT-017": "fold",
            "FLT-028": "annihilation",
            "FLT-044": "dark_thermal",
            "FLT-052": "shield",
            "FLT-061": "gravity",
        }[card_id]
        remaining[system] -= 1
    used = {card["id"] for card in pinned} | RESERVED
    free = [f"FLT-{i:03d}" for i in range(1, 101) if f"FLT-{i:03d}" not in used]
    order = [system for system in SYSTEM_QUOTAS if system != "sensors"]
    slots = [("sensors", "sensor_lie") for _ in range(remaining.pop("sensors"))]

    def take(role, count):
        guard = 0
        while count:
            progressed = False
            for system in order:
                if count == 0:
                    break
                if remaining[system] <= 0:
                    continue
                slots.append((system, role))
                remaining[system] -= 1
                count -= 1
                progressed = True
            guard += 1
            if not progressed or guard > 40:
                raise RuntimeError(f"could not place {role}, left {count}, {remaining}")

    take("confounder", 12)
    take("bridge", 17)
    for system in order:
        while remaining[system]:
            slots.append((system, "local"))
            remaining[system] -= 1
    if len(slots) != len(free) or any(remaining.values()):
        raise RuntimeError(f"slots {len(slots)} free {len(free)} remaining {remaining}")
    cards = []
    for serial, ((system, role), card_id) in enumerate(zip(slots, free), start=1):
        parts = PARTS[system]
        component = parts[serial % len(parts)]
        neighbor = COMPONENT_NAMES[parts[(serial + 1) % len(parts)]]
        trigger = FILLER_TRIGGERS[serial % len(FILLER_TRIGGERS)]
        mode = MODES[role][serial % len(MODES[role])]
        part = COMPONENT_NAMES[component]
        second = parts[(serial + 2) % len(parts)]
        components = [component]
        if role == "bridge" and second != component:
            components.append(second)
        symptoms = fit(
            f"{part}の{mode}が、{WHEN[trigger]}に基準から外れる。"
            f"外れは{part}の監視点に留まり、{neighbor}の同じ測点は基準内のままである。"
            f"条件を外すと指示は基準へ戻り、監視帯{serial}の記録に残る。"
        )
        cards.append(
            {
                "id": card_id,
                "name": f"{part}の{mode}",
                "symptoms": symptoms,
                "cause": f"{part}の内部状態が{mode}を維持し、{neighbor}へは同じ偏差を伝えない。",
                "severity": (serial % 5) + 1,
                "systems": system,
                "derived": [],
                "components": components,
                "triggers": [trigger],
                "role": role,
                "discriminators": [f"{WHEN[trigger]}以外では{part}の{mode}は再現しない。"],
            }
        )
    return cards


def assign_cycles(cards):
    by_system = {}
    for card in cards:
        if card["id"] in PAIRS:
            card["derived"] = PAIRS[card["id"]]
            continue
        by_system.setdefault(card["systems"], []).append(card)
    for group in by_system.values():
        if len(group) < 2:
            raise RuntimeError(group[0]["id"])
        ordered = sorted(group, key=lambda card: card["id"])
        for index, card in enumerate(ordered):
            card["derived"] = [ordered[(index + 1) % len(ordered)]["id"]]


def main():
    pinned = pinned_cards()
    generated = pinned + filler_cards(pinned)
    assign_cycles(generated)
    by_id = {card["id"]: card for card in generated}
    if len(by_id) != 94:
        raise RuntimeError(len(by_id))
    for path in FAULTS.glob("FLT-*.yaml"):
        if path.stem not in RESERVED and path.stem not in by_id:
            path.unlink()
    for card in generated:
        (FAULTS / f"{card['id']}.yaml").write_text(dump_card(card), encoding="utf-8")
    for card_id, targets in PAIRS.items():
        if card_id in RESERVED and card_id not in {"FLT-017", "FLT-044"}:
            replace_derived(FAULTS / f"{card_id}.yaml", targets)
    for path in COUPLINGS.glob("CPL-*.yaml"):
        if path.stem != "CPL-03":
            path.unlink()
    for note in notes():
        (COUPLINGS / f"{note['id']}.yaml").write_text(dump_note(note), encoding="utf-8")
    faults, couplings = load_corpus(ROOT / "data")
    issues = validate_corpus(faults, couplings, complete=True)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"faults {len(faults)} couplings {len(couplings)}")


if __name__ == "__main__":
    main()
