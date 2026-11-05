"""Écritures des number et des switch, avec relecture de confirmation."""

from __future__ import annotations

from homeassistant.components.number import ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.components.switch import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from modbus_connection import ModbusConnectionError
from modbus_connection.mock import WriteEvent
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pool_technologie.const import DOMAIN

from .conftest import FakeModbus, entry_data

NUMBERS = {
    # entité, valeur demandée, mot écrit, état publié
    "number.poolsquad_uv_ph_setpoint": (7.3, 4207, 18688, "7.3"),
    "number.poolsquad_uv_electrolysis_setpoint": (35, 4168, 35, "35"),
    "number.poolsquad_uv_ph_corrector_concentration": (20, 4208, 20, "20.0"),
    "number.poolsquad_uv_pool_size_setpoint": (52, 4111, 52, "52"),
    "number.poolsquad_uv_cell_inversion_time": (6, 4170, 6, "6"),
}


@pytest.fixture
async def loaded(hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry):
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return fake_modbus.unit()


async def set_value(hass: HomeAssistant, entity_id: str, value: float) -> None:
    await hass.services.async_call(
        "number", SERVICE_SET_VALUE, {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value}, blocking=True
    )


def state(hass: HomeAssistant, entity_id: str) -> str:
    current = hass.states.get(entity_id)
    assert current is not None
    return current.state


@pytest.mark.parametrize("entity_id", sorted(NUMBERS))
async def test_number_write(hass: HomeAssistant, loaded, entity_id: str) -> None:
    value, address, word, published = NUMBERS[entity_id]
    writes: list[WriteEvent] = []
    loaded.on_write(writes.append)
    loaded.read_events.clear()

    await set_value(hass, entity_id, value)

    assert writes == [WriteEvent("holding", address, [word], 0x06)]
    assert [(e.address, e.count) for e in loaded.read_events] == [(address, 1)]
    assert state(hass, entity_id) == published


async def test_orp_setpoint_write(hass: HomeAssistant, fake_modbus: FakeModbus) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, data=entry_data(regulation_orp=True), title="Poolsquad UV"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    await set_value(hass, "number.poolsquad_uv_orp_setpoint", 700)
    assert fake_modbus.holding[4235] == 700
    assert state(hass, "number.poolsquad_uv_orp_setpoint") == "700"


async def test_number_not_confirmed(
    hass: HomeAssistant, loaded, caplog: pytest.LogCaptureFixture
) -> None:
    loaded.on_write(lambda event: loaded.holding.__setitem__(4168, 20))
    await set_value(hass, "number.poolsquad_uv_electrolysis_setpoint", 55)

    assert state(hass, "number.poolsquad_uv_electrolysis_setpoint") == "20"
    assert "Consigne électrolyse non confirmée par l'appareil après écriture (55)" in caplog.text


async def test_number_write_failed(
    hass: HomeAssistant, loaded, caplog: pytest.LogCaptureFixture
) -> None:
    loaded.fail_write(4207, ModbusConnectionError("liaison coupée"))
    await set_value(hass, "number.poolsquad_uv_ph_setpoint", 7.5)

    assert state(hass, "number.poolsquad_uv_ph_setpoint") == "7.2"
    assert "Échec d'écriture de la consigne pH (raw=19200)" in caplog.text


async def switch(hass: HomeAssistant, entity_id: str, on: bool) -> None:
    await hass.services.async_call(
        "switch",
        SERVICE_TURN_ON if on else SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )


async def test_boost(hass: HomeAssistant, loaded) -> None:
    entity_id = "switch.poolsquad_uv_boost_mode"
    writes: list[WriteEvent] = []
    loaded.on_write(writes.append)

    await switch(hass, entity_id, True)
    assert state(hass, entity_id) == STATE_ON
    await switch(hass, entity_id, False)
    assert state(hass, entity_id) == STATE_OFF

    assert writes == [
        WriteEvent("holding", 4188, [1440], 0x06),
        WriteEvent("holding", 4182, [256], 0x06),
        WriteEvent("holding", 4188, [0], 0x06),
    ]


@pytest.mark.parametrize(
    ("on", "message"),
    [
        (True, "Activation du mode boost non confirmée par l'appareil"),
        (False, "Désactivation du mode boost non confirmée par l'appareil"),
    ],
)
async def test_boost_not_confirmed(
    hass: HomeAssistant, loaded, caplog: pytest.LogCaptureFixture, on: bool, message: str
) -> None:
    loaded.holding[4188] = 0 if on else 1440
    previous = loaded.holding[4188]
    loaded.on_write(lambda event: loaded.holding.__setitem__(4188, previous))
    before = state(hass, "switch.poolsquad_uv_boost_mode")

    await switch(hass, "switch.poolsquad_uv_boost_mode", on)

    assert state(hass, "switch.poolsquad_uv_boost_mode") == before
    assert message in caplog.text


@pytest.mark.parametrize(
    ("on", "message"),
    [(True, "Échec d'écriture du mode boost"), (False, "Échec de la désactivation du mode boost")],
)
async def test_boost_write_failed(
    hass: HomeAssistant, loaded, caplog: pytest.LogCaptureFixture, on: bool, message: str
) -> None:
    loaded.fail_write(4188, ModbusConnectionError("liaison coupée"))
    await switch(hass, "switch.poolsquad_uv_boost_mode", on)
    assert message in caplog.text


async def test_ph_auto(hass: HomeAssistant, loaded) -> None:
    entity_id = "switch.poolsquad_uv_automatic_ph_regulation"
    assert state(hass, entity_id) == STATE_ON

    await switch(hass, entity_id, False)
    assert loaded.holding[4200] == 0
    assert state(hass, entity_id) == STATE_OFF

    await switch(hass, entity_id, True)
    assert loaded.holding[4200] == 1
    assert state(hass, entity_id) == STATE_ON


@pytest.mark.parametrize(
    ("on", "message"),
    [
        (True, "Activation de la régulation pH automatique non confirmée par l'appareil"),
        (False, "Désactivation de la régulation pH automatique non confirmée par l'appareil"),
    ],
)
async def test_ph_auto_not_confirmed(
    hass: HomeAssistant, loaded, caplog: pytest.LogCaptureFixture, on: bool, message: str
) -> None:
    loaded.holding[4200] = previous = 0 if on else 1
    loaded.on_write(lambda event: loaded.holding.__setitem__(4200, previous))
    await switch(hass, "switch.poolsquad_uv_automatic_ph_regulation", on)
    assert message in caplog.text


@pytest.mark.parametrize(
    ("on", "message"),
    [
        (True, "Échec d'activation de la régulation pH automatique"),
        (False, "Échec de la désactivation de la régulation pH automatique"),
    ],
)
async def test_ph_auto_write_failed(
    hass: HomeAssistant, loaded, caplog: pytest.LogCaptureFixture, on: bool, message: str
) -> None:
    loaded.fail_write(4200, ModbusConnectionError("liaison coupée"))
    await switch(hass, "switch.poolsquad_uv_automatic_ph_regulation", on)
    assert message in caplog.text
