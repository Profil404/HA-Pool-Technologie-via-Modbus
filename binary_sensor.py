from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from .const import DOMAIN
from .models import MODELS

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    model_label = MODELS[config_entry.data["model"]]["name"]

    async_add_entities([
        ModbusStatusSensor(config_entry.entry_id, model_label, controller)
    ])

class ModbusStatusSensor(BinarySensorEntity):
    def __init__(self, entry_id, model_label, controller):
        self._entry_id = entry_id
        self._model_label = model_label
        self._controller = controller

        self._attr_has_entity_name = True
        self._attr_translation_key = "modbus_status"
        self._attr_unique_id = f"{entry_id}_modbus_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:lan-connect"
        self._attr_is_on = controller.modbus_ok

    @property
    def is_on(self):
        return self._attr_is_on

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }

    async def async_update(self):
        self._attr_is_on = self._controller.modbus_ok

