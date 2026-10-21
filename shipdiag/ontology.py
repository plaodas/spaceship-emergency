"""Closed identifiers from docs/01-technology.md and docs/02-card-rules.md."""

SYSTEM_QUOTAS = {
    "annihilation": 14,
    "fold": 12,
    "dark_thermal": 10,
    "gravity": 10,
    "comms": 10,
    "power": 8,
    "shield": 8,
    "life_support": 8,
    "sensors": 10,
    "hull": 10,
}

ROLE_QUOTAS = {
    "local": 55,
    "bridge": 20,
    "confounder": 15,
    "sensor_lie": 10,
}

COMPONENTS = frozenset(
    {
        "antimatter_bottle",
        "port_injector",
        "starboard_injector",
        "annihilation_chamber",
        "annihilation_jacket",
        "photon_nozzle",
        "starboard_fold_coil",
        "port_fold_coil",
        "mass_shadow_compensator",
        "dark_thermal_bus",
        "starboard_dark_valve",
        "port_dark_valve",
        "dark_matter_reservoir",
        "thermal_check_valve",
        "starboard_damper",
        "port_damper",
        "gravity_deck",
        "entanglement_bank",
        "phase_lock_array",
        "decoherence_shield",
        "zpe_bus",
        "starboard_power_leg",
        "starboard_shield_emitter",
        "port_shield_emitter",
        "starboard_habitat_duct",
        "port_habitat_duct",
        "atmosphere_loop",
        "hull_temp_sensor",
        "consumption_sensor",
        "phase_sensor",
        "starboard_hull",
        "port_hull",
        "hull_integrity_field",
    }
)

TRIGGERS = frozenset(
    {
        "steady",
        "after_jump",
        "during_jump",
        "during_burn",
        "high_power",
        "shield_on",
        "maneuver",
        "comms_active",
        "after_heat_pulse",
    }
)

COMPONENT_NAMES = {
    "antimatter_bottle": "反物質磁気瓶",
    "port_injector": "左舷噴射格子",
    "starboard_injector": "右舷噴射格子",
    "annihilation_chamber": "対消滅室",
    "annihilation_jacket": "対消滅室右舷ジャケット",
    "photon_nozzle": "光子ノズル",
    "starboard_fold_coil": "右舷折畳みコイル",
    "port_fold_coil": "左舷トリムコイル",
    "mass_shadow_compensator": "質量影補償器",
    "dark_thermal_bus": "暗黒熱バス",
    "starboard_dark_valve": "右舷暗黒熱弁",
    "port_dark_valve": "左舷暗黒熱弁",
    "dark_matter_reservoir": "ダークマター貯槽",
    "thermal_check_valve": "逆止弁",
    "starboard_damper": "右舷慣性ダンパー",
    "port_damper": "左舷慣性ダンパー",
    "gravity_deck": "擬似重力甲板",
    "entanglement_bank": "もつれ対バンク",
    "phase_lock_array": "位相ロックアレイ",
    "decoherence_shield": "デコヒーレンス遮蔽",
    "zpe_bus": "零点母線",
    "starboard_power_leg": "右舷給電レグ",
    "starboard_shield_emitter": "右舷シールドエミッタ",
    "port_shield_emitter": "左舷シールドエミッタ",
    "starboard_habitat_duct": "右舷居住区ダクト",
    "port_habitat_duct": "左舷居住区ダクト",
    "atmosphere_loop": "大気循環",
    "hull_temp_sensor": "外板温度センサー",
    "consumption_sensor": "反物質消費センサー",
    "phase_sensor": "位相センサー",
    "starboard_hull": "右舷外板",
    "port_hull": "左舷外板",
    "hull_integrity_field": "構造健全性フィールド",
}

SYSTEMS = frozenset(SYSTEM_QUOTAS)
ROLES = frozenset(ROLE_QUOTAS)

CREW_WORDS = ("燃費", "ワープ", "エンジンルーム", "警告灯", "右側", "左側")
