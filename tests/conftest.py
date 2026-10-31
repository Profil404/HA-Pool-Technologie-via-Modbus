"""Fixtures communes : Home Assistant de test et électrolyseur en mémoire."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Notre paquet custom_components, avant celui du dossier de test du plugin.
import custom_components  # noqa: F401
from custom_components.pool_technologie.const import DOMAIN
from custom_components.pool_technologie.pool_technologie_modbus import PoolTechnologieDevice

ENTRY_ID = "01TESTENTRY"

HOLDING = {
    259: 7234,  # pH 7,2
    260: 245,  # 24,5 °C
    261: 41,  # 4,1 g/L
    262: 700,  # 700 mV
    1061: 5000,
    1062: 3200,
    1063: 16,
    2050: 400,
    2051: 600,
    4111: 45,
    4168: 20,
    4170: 4,
    4182: 0,
    4188: 0,
    4200: 1,
    4207: 18432,  # pH 7,2
    4208: 15,
    4235: 650,
    4463: 1234,
}


class FakeModbus:
    """Ce que le modbus de Home Assistant ouvre : des connexions en mémoire.

    Toutes partagent les registres de ``holding``, comme un même appareil
    rejoint à chaque fois.
    """

    def __init__(self) -> None:
        self.holding: dict[int, Any] = dict(HOLDING)
        self.connections: list[MockModbusConnection] = []
        self.params: list[Any] = []
        self.failure: Exception | None = None

    def __call__(self, params: Any) -> MockModbusConnection:
        connection = MockModbusConnection()
        self.connections.append(connection)
        self.params.append(params)
        return connection

    @property
    def connection(self) -> MockModbusConnection:
        return self.connections[-1]

    def unit(self, unit_id: int = 1) -> MockModbusUnit:
        return self.connection.for_unit(unit_id)

    def fail(self, error: Exception | None) -> None:
        """Rend l'électrolyseur injoignable (ou de nouveau joignable)."""
        self.failure = error
        for connection in self.connections:
            for unit in connection._units.values():
                unit.fail_requests(error)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Charge les intégrations de custom_components."""


@pytest.fixture(autouse=True)
def no_write_settle() -> Generator[None]:
    with patch.object(PoolTechnologieDevice, "write_settle", 0):
        yield


@pytest.fixture
def fake_modbus() -> Generator[FakeModbus]:
    fake = FakeModbus()
    original = MockModbusConnection.for_unit

    def for_unit(connection: MockModbusConnection, unit_id: int) -> MockModbusUnit:
        new = unit_id not in connection._units
        unit = original(connection, unit_id)
        if new:
            unit.holding = fake.holding
            unit.fail_requests(fake.failure)
        return unit

    with (
        patch("homeassistant.components.modbus.connection.ModbusConnection", side_effect=fake),
        patch.object(MockModbusConnection, "for_unit", for_unit),
    ):
        yield fake


def entry_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "host": "192.168.1.50",
        "port": 502,
        "unit_id": 1,
        "model": "poolsquad_uv",
        "sonde_ph": True,
        "regulation_orp": False,
        "scan_interval": 60,
    }
    data.update(overrides)
    return data


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN, data=entry_data(), entry_id=ENTRY_ID, title="Poolsquad UV"
    )
