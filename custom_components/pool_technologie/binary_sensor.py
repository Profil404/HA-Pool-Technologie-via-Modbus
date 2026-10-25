from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory

from .entity import PoolTechnologieEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([ModbusStatusSensor(config_entry.runtime_data)])


class ModbusStatusSensor(PoolTechnologieEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator, None)

        self._attr_translation_key = "modbus_status"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_modbus_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:lan-connect"

    @property
    def available(self):
        # Le diagnostic de la communication reste lisible quand elle est coupée.
        return True

    @property
    def is_on(self):
        return self.coordinator.modbus_ok
