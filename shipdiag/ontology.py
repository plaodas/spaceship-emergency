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

SYSTEMS = frozenset(SYSTEM_QUOTAS)
ROLES = frozenset(ROLE_QUOTAS)

CREW_WORDS = ("燃費", "ワープ", "エンジンルーム", "警告灯", "右側", "左側")
