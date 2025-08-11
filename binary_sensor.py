from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from .const import DOMAIN
from .models import MODELS

FAILURE_THRESHOLD = 5 

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    model_label = MODELS[config_entry.data["model"]]["name"]
    filtration_entity = config_entry.options.get("filtration_entity") or config_entry.data.get("filtration_entity")

    async_add_entities([
        ModbusStatusSensor(config_entry.entry_id, model_label, controller, filtration_entity, hass)
    ])

class ModbusStatusSensor(BinarySensorEntity):
    def __init__(self, entry_id, model_label, controller, filtration_entity, hass):
        self._entry_id = entry_id
        self._model_label = model_label
        self._controller = controller
        self._filtration_entity = filtration_entity
        self.hass = hass

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
        if self._filtration_entity:
            state = self.hass.states.get(self._filtration_entity)
            if state is None or state.state != "on":
                self._attr_is_on = False
                return

        self._attr_is_on = self._controller.modbus_ok

