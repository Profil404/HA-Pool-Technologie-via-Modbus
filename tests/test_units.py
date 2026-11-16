"""Conversion d'unité des capteurs (°F, kW) et restauration de leur valeur."""

from __future__ import annotations

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from modbus_connection import ModbusConnectionError
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

from custom_components.pool_technologie.const import DOMAIN

from .conftest import FakeModbus

TEMPERATURE = "sensor.poolsquad_uv_water_temperature"
POWER = "sensor.poolsquad_uv_cell_power"


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


def choose_unit(
    hass: HomeAssistant, entry: MockConfigEntry, unique_id: str, entity_id: str, unit: str
) -> None:
    """L'unité choisie par l'utilisateur dans les réglages de l'entité."""
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registered = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        unique_id,
        config_entry=entry,
        suggested_object_id=entity_id.removeprefix("sensor."),
    )
    assert registered.entity_id == entity_id
    registry.async_update_entity_options(entity_id, "sensor", {"unit_of_measurement": unit})


def value_and_unit(hass: HomeAssistant, entity_id: str) -> tuple[float, str]:
    current = hass.states.get(entity_id)
    assert current is not None, entity_id
    return float(current.state), current.attributes[ATTR_UNIT_OF_MEASUREMENT]


async def test_units_chosen_by_user_are_converted(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    """24,5 °C s'affiche 76,1 °F, et non 24,5 °F ; 16 W s'affichent 0,016 kW."""
    choose_unit(hass, config_entry, "temperature_eau", TEMPERATURE, UnitOfTemperature.FAHRENHEIT)
    choose_unit(hass, config_entry, "puissance_cellule", POWER, UnitOfPower.KILO_WATT)
    await setup(hass, config_entry)

    value, unit = value_and_unit(hass, TEMPERATURE)
    assert (value, unit) == (pytest.approx(76.1), UnitOfTemperature.FAHRENHEIT)
    value, unit = value_and_unit(hass, POWER)
    assert (value, unit) == (pytest.approx(0.016), UnitOfPower.KILO_WATT)


async def test_imperial_system_keeps_celsius(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    """En système impérial, la température reste en °C, comme avant.

    La classe d'appareil est déclarée en texte ("temperature") : Home Assistant
    ne lui applique pas sa conversion automatique vers l'unité du système.
    """
    hass.config.units = US_CUSTOMARY_SYSTEM
    await setup(hass, config_entry)

    value, unit = value_and_unit(hass, TEMPERATURE)
    assert (value, unit) == (pytest.approx(24.5), UnitOfTemperature.CELSIUS)


async def test_device_off_restores_native_value(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    """La valeur restaurée est celle de l'appareil (°C), reconvertie à l'affichage."""
    choose_unit(hass, config_entry, "temperature_eau", TEMPERATURE, UnitOfTemperature.FAHRENHEIT)
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(TEMPERATURE, "71.6", {ATTR_UNIT_OF_MEASUREMENT: "°F"}),
                {"native_value": 22.0, "native_unit_of_measurement": "°C"},
            )
        ],
    )
    fake_modbus.fail(ModbusConnectionError("injoignable"))
    await setup(hass, config_entry)

    value, unit = value_and_unit(hass, TEMPERATURE)
    assert (value, unit) == (pytest.approx(71.6), UnitOfTemperature.FAHRENHEIT)


async def test_device_off_restores_state_saved_before_fix(
    hass: HomeAssistant, fake_modbus: FakeModbus, config_entry: MockConfigEntry
) -> None:
    """Jusqu'à la 261108, l'état publié était la valeur en °C, même affichée en °F."""
    choose_unit(hass, config_entry, "temperature_eau", TEMPERATURE, UnitOfTemperature.FAHRENHEIT)
    mock_restore_cache(hass, [State(TEMPERATURE, "22.0", {ATTR_UNIT_OF_MEASUREMENT: "°F"})])
    fake_modbus.fail(ModbusConnectionError("injoignable"))
    await setup(hass, config_entry)

    value, unit = value_and_unit(hass, TEMPERATURE)
    assert (value, unit) == (pytest.approx(71.6), UnitOfTemperature.FAHRENHEIT)
