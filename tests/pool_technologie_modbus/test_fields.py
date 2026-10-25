"""Décodage, échelles et filtrage hors plage, contre les formules d'origine."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from custom_components.pool_technologie.pool_technologie_modbus import (
    PoolTechnologieDevice,
    Register,
    register,
)
from custom_components.pool_technologie.pool_technologie_modbus.components import (
    PH_SETPOINT_SCALE,
)

LIBRARY = Path(__file__).parents[2] / "custom_components/pool_technologie/pool_technologie_modbus"


def sensor_v261029(raw: int, scale: float, precision: int, low: float | None, high: float | None):
    """sensor.py v261029 : PoolSensor.update()."""
    value = round(raw * scale, precision)
    if (low is not None and value < low) or (high is not None and value > high):
        return None
    return value


def number_v261029(value: float, low: float, high: float):
    """number.py v261029 : _async_poll_refresh()."""
    return value if low <= value <= high else None


# Champ -> décodage d'origine, pour chaque valeur brute possible.
ORIGINAL = {
    "ph": lambda raw: sensor_v261029(raw, 0.001, 1, 0, 14),
    "water_temperature": lambda raw: sensor_v261029(raw, 0.1, 1, -10, 60),
    "salt": lambda raw: sensor_v261029(raw, 0.1, 1, 0, 20),
    "orp": lambda raw: sensor_v261029(raw, 1, 0, 0, 1200),
    "reported_pool_volume": lambda raw: sensor_v261029(raw, 1, 0, None, None),
    "reported_ph_setpoint": lambda raw: sensor_v261029(raw, 0.000390625, 1, 0, 14),
    "reported_orp_setpoint": lambda raw: sensor_v261029(raw, 1, 0, 0, 1200),
    "cell_voltage": lambda raw: sensor_v261029(raw, 1, 0, 0, 30000),
    "cell_current": lambda raw: sensor_v261029(raw, 1, 0, 0, 50000),
    "cell_power": lambda raw: sensor_v261029(raw, 1, 0, 0, 5000),
    "electrolysis_ratio": lambda raw: sensor_v261029(raw, 0.125, 0, 0, 100),
    "uv_ratio": lambda raw: sensor_v261029(raw, 0.125, 0, 0, 100),
    "operating_hours": lambda raw: sensor_v261029(raw, 1, 0, 0, 100000),
    "ph_setpoint": lambda raw: number_v261029(round(raw * 0.000390625, 2), 6.0, 8.5),
    "orp_setpoint": lambda raw: number_v261029(int(raw), 400, 900),
    "electrolysis_setpoint": lambda raw: number_v261029(int(raw), 10, 100),
    "ph_corrector_concentration": lambda raw: number_v261029(round(raw, 1), 5, 50),
    "pool_volume": lambda raw: number_v261029(int(round(raw)), 1, 250),
    "cell_inversion_interval": lambda raw: number_v261029(int(round(raw)), 1, 24),
    "boost_remaining": lambda raw: raw,
    "boost_flag": lambda raw: raw,
    "ph_regulation": lambda raw: raw,
}

ADDRESSES = {
    "ph": 259,
    "water_temperature": 260,
    "salt": 261,
    "orp": 262,
    "reported_pool_volume": 4111,
    "reported_ph_setpoint": 4207,
    "reported_orp_setpoint": 4235,
    "cell_voltage": 1061,
    "cell_current": 1062,
    "cell_power": 1063,
    "electrolysis_ratio": 2051,
    "uv_ratio": 2050,
    "operating_hours": 4463,
    "ph_setpoint": 4207,
    "orp_setpoint": 4235,
    "electrolysis_setpoint": 4168,
    "ph_corrector_concentration": 4208,
    "pool_volume": 4111,
    "cell_inversion_interval": 4170,
    "boost_remaining": 4188,
    "boost_flag": 4182,
    "ph_regulation": 4200,
}


def test_every_field_is_covered(mock_modbus_unit) -> None:
    device = PoolTechnologieDevice(mock_modbus_unit)
    assert set(device.field_names) == set(ORIGINAL) == set(ADDRESSES)


@pytest.mark.parametrize("name", sorted(ORIGINAL))
def test_decode_matches_original_for_every_raw_value(mock_modbus_unit, name: str) -> None:
    device = PoolTechnologieDevice(mock_modbus_unit)
    field = device.field(name)
    assert field.address == ADDRESSES[name]
    for raw in range(0x10000):
        got = field.decode([raw])
        expected = ORIGINAL[name](raw)
        # Même valeur, et même type : un int reste un int (état "12", pas "12.0").
        assert got == expected and type(got) is type(expected), (name, raw, got, expected)


def test_registers_are_unsigned() -> None:
    # Une température négative brute (complément à deux) sort de la plage,
    # comme avec le code d'origine qui lisait tout en non signé.
    temperature = register(260, scale=0.1, precision=1, valid=(-10, 60))
    assert temperature.decode([0xFFCE]) is None  # -5,0 °C en signé


@pytest.mark.parametrize(
    ("name", "value", "raw"),
    [
        ("ph_setpoint", 7.2, 18432),
        ("ph_setpoint", 7.3, 18688),
        ("ph_setpoint", 6.0, 15360),
        ("orp_setpoint", 650.0, 650),
        ("orp_setpoint", 655.9, 655),  # int() comme avant : tronqué
        ("electrolysis_setpoint", 20.7, 20),  # tronqué
        ("ph_corrector_concentration", 15.6, 16),  # arrondi
        ("pool_volume", 30.4, 30),
        ("cell_inversion_interval", 4.5, 4),  # round() de Python : au pair
    ],
)
def test_to_raw_matches_original(mock_modbus_unit, name: str, value: float, raw: int) -> None:
    field = PoolTechnologieDevice(mock_modbus_unit).field(name)
    assert field.to_raw(value) == raw
    assert field.encode(value) == [raw]


def test_to_raw_rejects_out_of_range_words() -> None:
    field = Register(4111, writable=True)
    field.name = "pool_volume"
    with pytest.raises(ValueError, match="hors de 0-65535"):
        field.to_raw(70000)
    with pytest.raises(ValueError):
        field.to_raw(-1)


def test_ph_setpoint_scale_is_one_over_2560() -> None:
    assert PH_SETPOINT_SCALE == 1 / 2560


def test_library_does_not_import_home_assistant() -> None:
    for path in LIBRARY.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            assert not any(n.split(".")[0] == "homeassistant" for n in names), path
        assert "home assistant" not in path.read_text(encoding="utf-8").lower(), path
