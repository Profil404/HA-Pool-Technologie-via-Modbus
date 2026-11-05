"""Flux de configuration et flux d'options."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.components.modbus import async_get_unit
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from modbus_connection import ModbusConnectionError, ModbusTimeoutError, ModbusTlsParams
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pool_technologie.const import DOMAIN

from .conftest import FakeModbus, entry_data

USER_INPUT = {
    "host": "192.168.1.50",
    "port": 502,
    "unit_id": 1,
    "model": "poolsquad_uv",
    "sonde_ph": True,
    "regulation_orp": False,
    "scan_interval": 60,
}


async def start(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    return result


async def test_user_flow(hass: HomeAssistant, fake_modbus: FakeModbus) -> None:
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Poolsquad UV"
    # Mêmes clés qu'avant la migration.
    assert result["data"] == USER_INPUT
    # La sonde de validation a lu l'appareil, puis rendu la connexion.
    validation = fake_modbus.connections[0]
    assert [(e.address, e.count) for e in validation.for_unit(1).read_events] == [(260, 1)]
    assert validation._closed


@pytest.mark.parametrize("error", [ModbusConnectionError("refus"), ModbusTimeoutError("délai")])
async def test_cannot_connect_then_recover(
    hass: HomeAssistant, fake_modbus: FakeModbus, error: Exception
) -> None:
    result = await start(hass)
    fake_modbus.fail(error)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    fake_modbus.fail(None)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_link_conflict(hass: HomeAssistant, fake_modbus: FakeModbus) -> None:
    other = MockConfigEntry(domain="other")
    other.add_to_hass(hass)
    async_get_unit(hass, other, ModbusTlsParams(host="192.168.1.50", port=502), 1)

    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "link_conflict"}


async def test_already_configured(hass: HomeAssistant, fake_modbus: FakeModbus) -> None:
    MockConfigEntry(domain=DOMAIN, data=entry_data()).add_to_hass(hass)

    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert fake_modbus.connections == []


async def test_other_unit_on_same_gateway(hass: HomeAssistant, fake_modbus: FakeModbus) -> None:
    MockConfigEntry(domain=DOMAIN, data=entry_data()).add_to_hass(hass)

    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, "unit_id": 2}
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize("bad", [{"port": 0}, {"port": 70000}, {"unit_id": 256}])
async def test_rejects_invalid_port_and_unit(
    hass: HomeAssistant, fake_modbus: FakeModbus, bad: dict[str, int]
) -> None:
    result = await start(hass)
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(result["flow_id"], {**USER_INPUT, **bad})


async def test_options_flow(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"]({})
    assert schema == {"sonde_ph": True, "regulation_orp": False, "scan_interval": 60}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"sonde_ph": False, "regulation_orp": True, "scan_interval": 120}
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"sonde_ph": False, "regulation_orp": True, "scan_interval": 120}
    # Rechargée avec les nouvelles options : une entité ORP ; l'entité pH n'est
    # plus fournie et reste au registre, indisponible, comme en v261029.
    ph = hass.states.get("sensor.poolsquad_uv_ph")
    assert ph is not None and ph.state == STATE_UNAVAILABLE and ph.attributes["restored"]
    orp = hass.states.get("sensor.poolsquad_uv_orp")
    assert orp is not None and orp.state == "700"
