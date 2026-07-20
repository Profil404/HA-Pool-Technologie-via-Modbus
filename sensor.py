import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN
from .models import MODELS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    model_key = data["model"]
    controller = data["controller"]
    handler = controller.handler  # même connexion que number.py, pas de client dupliqué

    sensors = [
        PoolSensor(hass, sensor_conf, handler, config_entry.entry_id, MODELS[model_key]["name"])
        for sensor_conf in MODELS[model_key]["sensors"]
    ]

    async_add_entities(sensors)

    async def update_sensors(now):
        for sensor in sensors:
            # read_register est bloquant (pymodbus synchrone) : on le sort de
            # la boucle asyncio de HA pour ne pas la geler pendant un timeout Modbus.
            await hass.async_add_executor_job(sensor.update)
            sensor.async_write_ha_state()

    controller._update_callback = update_sensors

class PoolSensor(SensorEntity, RestoreEntity):
    def __init__(self, hass, config, handler, entry_id, model_label):
        self.hass = hass
        self._config = config
        self._handler = handler
        self._entry_id = entry_id
        self._model_label = model_label
        self._state = None

        self._attr_translation_key = config.get("translation_key")
        self._attr_has_entity_name = True
        self._attr_icon = config.get("icon", "mdi:water")
        self._attr_native_unit_of_measurement = config.get("unit", "")
        self._attr_unique_id = config["unique_id"]
        # Le rafraîchissement est piloté par le controller (async_track_time_interval),
        # pas par le mécanisme de polling natif de HA : pas besoin que HA nous appelle aussi.
        self._attr_should_poll = False

        self._attr_device_class = config.get("device_class")

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label
        }

    async def async_added_to_hass(self):
        last_state = await self.async_get_last_state()
        if last_state and self._state is None:
            try:
                self._state = float(last_state.state)
            except ValueError:
                pass
                
    def update(self):
        """Tourne dans un thread executor : ne jamais appeler depuis la boucle asyncio."""
        controller = self.hass.data[DOMAIN][self._entry_id]["controller"]
        result = self._handler.read_register(self._config["address"])

        if result is None:
            controller.notify_modbus_failure()
            return

        value = round(result[0] * self._config.get("scale", 1), self._config.get("precision", 0))

        min_valid = self._config.get("min_valid")
        max_valid = self._config.get("max_valid")
        if (min_valid is not None and value < min_valid) or (max_valid is not None and value > max_valid):
            _LOGGER.debug(
                "Lecture hors plage ignorée pour %s: %s", self._config["unique_id"], value
            )
            controller.notify_modbus_failure()
            return

        self._state = value
        controller.notify_modbus_success()
