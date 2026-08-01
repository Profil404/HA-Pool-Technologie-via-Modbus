import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN, CONF_REGULATION_ORP
from .models import MODELS

_LOGGER = logging.getLogger(__name__)

# Capteurs sans intérêt si aucune sonde ORP n'est installée
_ORP_SENSOR_KEYS = {"orp", "consigne_orp"}


async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    model_key = data["model"]
    controller = data["controller"]
    handler = controller.handler  # même connexion que number.py, pas de client dupliqué

    regulation_orp = config_entry.options.get(
        CONF_REGULATION_ORP, config_entry.data.get(CONF_REGULATION_ORP, False)
    )

    sensors = [
        PoolSensor(hass, sensor_conf, handler, config_entry.entry_id, MODELS[model_key]["name"])
        for sensor_conf in MODELS[model_key]["sensors"]
        if regulation_orp or sensor_conf.get("translation_key") not in _ORP_SENSOR_KEYS
    ]

    async_add_entities(sensors)

    async def update_sensors(now):
        if controller.should_skip_poll():
            return
        any_success = False
        for sensor in sensors:
            # read_register est bloquant (pymodbus synchrone) : on le sort de
            # la boucle asyncio de HA pour ne pas la geler pendant un timeout Modbus.
            ok = await hass.async_add_executor_job(sensor.update)
            if ok:
                any_success = True
            sensor.async_write_ha_state()
        # Rafraîchit les entités d'autres plateformes (switch.py, number.py) sur le même
        # cycle, au lieu de les laisser gérer leur propre polling natif HA à un rythme différent.
        for poll_listener in list(controller._poll_listeners):
            if await poll_listener():
                any_success = True
        # Un seul appel par cycle : une lecture isolée en échec (registre ponctuellement
        # invalide) ne doit pas, à elle seule, faire avancer le compteur de déconnexion
        # si d'autres lectures du même cycle ont réussi.
        if any_success:
            controller.notify_modbus_success()
        else:
            controller.notify_modbus_failure()

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
        if config.get("entity_category") == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {"modbus_address": self._config["address"]}

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
                
    def update(self) -> bool:
        """Tourne dans un thread executor : ne jamais appeler depuis la boucle asyncio.

        Retourne True/False (succès/échec) ; c'est update_sensors() qui décide, une
        fois par cycle, d'appeler controller.notify_modbus_success/failure.
        """
        result = self._handler.read_register(self._config["address"])

        if result is None:
            return False

        value = round(result[0] * self._config.get("scale", 1), self._config.get("precision", 0))

        min_valid = self._config.get("min_valid")
        max_valid = self._config.get("max_valid")
        if (min_valid is not None and value < min_valid) or (max_valid is not None and value > max_valid):
            _LOGGER.debug(
                "Lecture hors plage ignorée pour %s: %s", self._config["unique_id"], value
            )
            return False

        self._state = value
        return True
