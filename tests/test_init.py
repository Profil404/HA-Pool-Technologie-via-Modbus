"""Setup, déchargement, rechargement et disponibilité."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.modbus import async_get_unit
from homeassistant.components.modbus.connection import async_get_connection_info
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusTimeoutError,
    ModbusTcpParams,
    ModbusTlsParams,
)
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
)

from custom_components.pool_technologie.const import DOMAIN
from custom_components.pool_technologie.coordinator import PoolTechnologieCoordinator
from custom_components.pool_technologie.pool_technologie_modbus import PoolTechnologieDevice

from .conftest import FakeModbus, entry_data

PH = "sensor.poolsquad_uv_ph"
SALT = "sensor.poolsquad_uv_salt_level"
TEMPERATURE = "sensor.poolsquad_uv_water_temperature"
ORP_SETPOINT = "number.poolsquad_uv_ph_setpoint"
BOOST = "switch.poolsquad_uv_boost_mode"
STATUS = "binary_sensor.poolsquad_uv_modbus_communication_status"


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


async def next_cycle(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int = 60
) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    # Le rafraîchissement périodique du coordinator est une tâche de fond.
    await hass.async_block_till_done(wait_background_tasks=True)


def state(hass: HomeAssistant, entity_id: str) -> str:
    current = hass.states.get(entity_id)
    assert current is not None, entity_id
    return current.state


async def test_setup_and_unload(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    await setup(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert isinstance(config_entry.runtime_data, PoolTechnologieCoordinator)
    # Une unité sur la connexion partagée du modbus de Home Assistant, en
    # Modbus TCP natif (MBAP) comme le client pymodbus d'avant.
    assert fake_modbus.params == [ModbusTcpParams(host="192.168.1.50", port=502)]
    assert fake_modbus.params[0].framer == "socket"
    assert [info.units for info in async_get_connection_info(hass)] == [
        {config_entry.entry_id: [1]}
    ]
    assert state(hass, PH) == "7.2"
    assert state(hass, TEMPERATURE) == "24.5"
    assert state(hass, ORP_SETPOINT) == "7.2"
    assert state(hass, STATUS) == STATE_ON

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert config_entry.state is ConfigEntryState.NOT_LOADED
    # Le dernier détenteur s'est déchargé : Home Assistant a fermé la connexion.
    assert fake_modbus.connection._closed
    assert async_get_connection_info(hass) == []


async def test_setup_does_not_wait_for_first_read(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    """Électrolyseur lent ou éteint : le setup ne l'attend pas (#12)."""
    release = asyncio.Event()
    original = PoolTechnologieDevice.async_update

    async def slow(self: PoolTechnologieDevice) -> Any:
        await release.wait()
        return await original(self)

    with patch.object(PoolTechnologieDevice, "async_update", slow):
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state is ConfigEntryState.LOADED
        assert state(hass, PH) == "unknown"
        release.set()
        await hass.async_block_till_done(wait_background_tasks=True)
    assert state(hass, PH) == "7.2"


async def test_reload(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    await setup(hass, config_entry)
    before = {
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)
    }

    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert config_entry.state is ConfigEntryState.LOADED
    assert len(fake_modbus.connections) == 2
    assert fake_modbus.connections[0]._closed
    assert not fake_modbus.connections[1]._closed
    after = {
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), config_entry.entry_id)
    }
    assert after == before
    assert state(hass, PH) == "7.2"


async def test_options_change_reloads_with_new_interval(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup(hass, config_entry)
    hass.config_entries.async_update_entry(
        config_entry, options={"sonde_ph": True, "regulation_orp": True, "scan_interval": 30}
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    assert config_entry.runtime_data.update_interval == timedelta(seconds=30)
    assert hass.states.get("sensor.poolsquad_uv_orp") is not None
    fake_modbus.holding[259] = 7500
    await next_cycle(hass, freezer, 30)
    assert state(hass, PH) == "7.5"


async def test_link_conflict_retries_setup(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    # Une autre entrée tient déjà la passerelle avec d'autres paramètres de liaison.
    other = MockConfigEntry(domain="other")
    other.add_to_hass(hass)
    async_get_unit(hass, other, ModbusTlsParams(host="192.168.1.50", port=502), 1)

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_device_off_at_startup(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Pompe coupée la nuit : le setup aboutit, les entités se remplissent au retour."""
    mock_restore_cache(hass, [State(PH, "7.1")])
    fake_modbus.fail(ModbusConnectionError("injoignable"))
    await setup(hass, config_entry)

    assert config_entry.state is ConfigEntryState.LOADED
    assert state(hass, PH) == "7.1"  # dernière valeur restaurée
    assert state(hass, ORP_SETPOINT) == "7.2"  # valeur initiale
    assert state(hass, STATUS) == STATE_OFF

    fake_modbus.fail(None)
    await next_cycle(hass, freezer)
    assert state(hass, PH) == "7.2"
    assert state(hass, STATUS) == STATE_ON


async def test_outage_keeps_last_values_then_back(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Comme en v261029 : dernières valeurs gardées, seul l'état de la communication change."""
    await setup(hass, config_entry)
    fake_modbus.fail(ModbusConnectionError("passerelle coupée"))

    # Deux cycles ratés : communication encore "on".
    for _ in range(2):
        await next_cycle(hass, freezer)
        assert state(hass, PH) == "7.2"
        assert state(hass, BOOST) == STATE_OFF
        assert state(hass, STATUS) == STATE_ON

    # Troisième : le diagnostic passe à "off", les entités gardent leur valeur.
    await next_cycle(hass, freezer)
    assert state(hass, STATUS) == STATE_OFF
    for _ in range(3):
        await next_cycle(hass, freezer)
    assert state(hass, PH) == "7.2"
    assert state(hass, SALT) == "4.1"
    assert state(hass, ORP_SETPOINT) == "7.2"
    assert state(hass, BOOST) == STATE_OFF
    # Un seul avertissement pour toute la coupure.
    assert caplog.text.count("injoignable depuis 3 cycles") == 1

    # Retour de la passerelle : sans rechargement de l'entrée.
    fake_modbus.holding[259] = 7400
    fake_modbus.fail(None)
    await next_cycle(hass, freezer)
    assert config_entry.state is ConfigEntryState.LOADED
    assert state(hass, PH) == "7.4"
    assert state(hass, BOOST) == STATE_OFF
    assert state(hass, STATUS) == STATE_ON
    assert len(fake_modbus.connections) == 1
    assert "Communication Modbus rétablie" in caplog.text


async def test_connection_lost_reconnects_on_next_request(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Issue #7 : la passerelle ferme la session, la requête suivante la rouvre."""
    await setup(hass, config_entry)
    fake_modbus.connection.simulate_connection_lost()
    assert not fake_modbus.connection.connected

    fake_modbus.holding[261] = 45
    await next_cycle(hass, freezer)
    assert fake_modbus.connection.connected
    assert state(hass, SALT) == "4.5"
    assert state(hass, STATUS) == STATE_ON


async def test_one_failed_register_only_affects_its_entity(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup(hass, config_entry)
    fake_modbus.unit().fail_read(259, IllegalDataAddressError())
    fake_modbus.holding.update({259: 7500, 261: 45})
    await next_cycle(hass, freezer)

    assert state(hass, PH) == "7.2"  # dernière valeur connue
    assert state(hass, SALT) == "4.5"
    assert state(hass, STATUS) == STATE_ON


async def test_out_of_range_keeps_last_value(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    await setup(hass, config_entry)
    fake_modbus.holding.update({259: 14100, 4207: 25600})  # pH 14,1 ; consigne 10,0
    await next_cycle(hass, freezer)

    assert state(hass, PH) == "7.2"
    assert state(hass, ORP_SETPOINT) == "7.2"  # hors réglage (6,0-8,5)
    assert state(hass, "sensor.poolsquad_uv_ph_setpoint") == "10.0"  # dans 0-14


async def test_disabled_entities_are_not_read(
    hass: HomeAssistant, fake_modbus: FakeModbus, freezer: FrozenDateTimeFactory
) -> None:
    # Sur l'iBasel Duo, courant, puissance et ratios cellule sont non testés :
    # créés désactivés, donc jamais lus.
    entry = MockConfigEntry(domain=DOMAIN, data=entry_data(model="ibasel_duo"), title="iBasel")
    await setup(hass, entry)
    unit = fake_modbus.unit()
    unit.read_events.clear()
    await next_cycle(hass, freezer)

    read = [(event.address, event.count) for event in unit.read_events]
    assert read == [
        (4111, 1),
        (259, 1),
        (260, 1),
        (261, 1),
        (4207, 1),
        (4208, 1),
        (4188, 1),
        (4200, 1),
    ]


async def test_nothing_selected_counts_as_failed(
    hass: HomeAssistant, fake_modbus: FakeModbus, freezer: FrozenDateTimeFactory
) -> None:
    """Comme avant : un cycle sans aucune lecture réussie compte comme raté."""
    entry = MockConfigEntry(domain=DOMAIN, data=entry_data(), title="Poolsquad UV")
    await setup(hass, entry)
    registry = er.async_get(hass)
    coordinator = entry.runtime_data
    coordinator.device.select([])
    for _ in range(3):
        await coordinator.async_refresh()
    assert coordinator.last_update_success  # jamais d'indisponibilité
    assert not coordinator.modbus_ok
    assert registry.async_get(STATUS) is not None
    assert state(hass, STATUS) == STATE_OFF


@pytest.mark.parametrize("partial", [IllegalDataAddressError()])
async def test_every_register_refused_counts_as_failed(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    partial: Exception,
) -> None:
    await setup(hass, config_entry)
    fake_modbus.fail(partial)
    for _ in range(3):
        await next_cycle(hass, freezer)
    assert state(hass, PH) == "7.2"
    assert state(hass, STATUS) == STATE_OFF


async def test_device_silent_mid_cycle_stops_the_cycle(
    hass: HomeAssistant,
    fake_modbus: FakeModbus,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Électrolyseur éteint en cours de cycle : on s'arrête, comme en v261029."""
    await setup(hass, config_entry)
    unit = fake_modbus.unit()
    fake_modbus.holding.update({4111: 50, 261: 45})
    unit.fail_read(260, ModbusTimeoutError("pas de réponse"))
    unit.read_events.clear()
    await next_cycle(hass, freezer)

    # 4111 et 259 lus, 260 sans réponse : le reste du cycle n'est pas tenté.
    assert [e.address for e in unit.read_events] == [4111, 259, 260]
    assert state(hass, "sensor.poolsquad_uv_pool_size") == "50"  # lu avant l'arrêt
    assert state(hass, SALT) == "4.1"  # pas relu, dernière valeur gardée


async def test_non_numeric_restored_state_is_ignored(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    mock_restore_cache(hass, [State(PH, STATE_UNAVAILABLE)])
    fake_modbus.fail(ModbusConnectionError("injoignable"))
    await setup(hass, config_entry)
    assert state(hass, PH) == "unknown"
