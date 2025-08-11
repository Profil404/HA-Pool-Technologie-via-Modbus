from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfElectricPotential
import asyncio

from .models import MODELS
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    model_label = MODELS[config_entry.data["model"]]["name"]
    handler = controller.handler

    entities = [
        ORPSetpointEntity(hass, handler, config_entry.entry_id, model_label),
        PHSetpointEntity(hass, handler, config_entry.entry_id, model_label),
    ]
    async_add_entities(entities)

class ORPSetpointEntity(NumberEntity):
    def __init__(self, hass, handler, entry_id, model_label):
        self._hass = hass
        self._handler = handler
        self._entry_id = entry_id
        self._model_label = model_label
        self._address = 4235

        self._attr_translation_key = "consigne_orp"
        self._attr_has_entity_name = True
        self._attr_entity_category = None
        self._attr_icon = "mdi:cog"
        self._attr_unique_id = f"{entry_id}_consigne_orp"
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.MILLIVOLT
        self._attr_mode = "box"
        self._attr_native_value = 650

    @property
    def native_min_value(self):
        return 400

    @property
    def native_max_value(self):
        return 900

    @property
    def native_step(self):
        return 10

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }

    async def async_added_to_hass(self):
        result = self._handler.read_register(self._address)
        if result:
            self._attr_native_value = int(result[0])

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = int(value)
        self._handler.write_register(self._address, int(value))
        await asyncio.sleep(0.5)

class PHSetpointEntity(NumberEntity):
    def __init__(self, hass, handler, entry_id, model_label):
        self._hass = hass
        self._handler = handler
        self._entry_id = entry_id
        self._model_label = model_label
        self._address = 4207
        self._scale = 0.000390625

        self._attr_translation_key = "consigne_ph"
        self._attr_has_entity_name = True
        self._attr_entity_category = None
        self._attr_icon = "mdi:cog"
        self._attr_unique_id = f"{entry_id}_consigne_ph"
        self._attr_native_unit_of_measurement = "pH"
        self._attr_mode = "box"
        self._attr_native_value = 7.2

    @property
    def native_min_value(self):
        return 6.0

    @property
    def native_max_value(self):
        return 8.5

    @property
    def native_step(self):
        return 0.1

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }

    async def async_added_to_hass(self):
        result = self._handler.read_register(self._address)
        if result:
            raw = result[0]
            self._attr_native_value = round(raw * self._scale, 2)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        raw = int(round(value / self._scale))
        self._handler.write_register(self._address, raw)
        await asyncio.sleep(0.5)