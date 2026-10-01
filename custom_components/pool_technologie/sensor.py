import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN
from .models import MODELS, SENSORS, PH_SENSOR_KEYS, ORP_SENSOR_KEYS, entity_status
from .options_helper import has_ph_probe, has_orp_probe

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    model_key = data["model"]
    controller = data["controller"]
    handler = controller.handler  # même connexion que number.py, pas de client dupliqué

    ph_probe = has_ph_probe(config_entry)
    orp_probe = has_orp_probe(config_entry)

    sensors = []
    for sensor_conf in SENSORS:
        key = sensor_conf["translation_key"]
        if key in PH_SENSOR_KEYS and not ph_probe:
            continue
        if key in ORP_SENSOR_KEYS and not orp_probe:
            continue
        create, enabled_default = entity_status(sensor_conf, model_key)
        if not create:
            continue
        sensors.append(
            PoolSensor(
                hass, sensor_conf, handler, config_entry.entry_id,
                MODELS[model_key]["name"], enabled_default,
            )
        )

    async_add_entities(sensors)

    async def update_sensors(now):
        if controller.should_skip_poll():
            return
        any_success = False
        for sensor in sensors:
            # Entité désactivée (par défaut ou par l'utilisateur) : jamais ajoutée à HA,
            # donc ni lecture Modbus ni écriture d'état.
            if not sensor.is_active:
                continue
            # read_register est bloquant (pymodbus synchrone) : on le sort de
            # la boucle asyncio de HA pour ne pas la geler pendant un timeout Modbus.
            ok = await hass.async_add_executor_job(sensor.update)
            if ok:
                any_success = True
            sensor.async_write_ha_state()
        # Rafraîchit les entités d'autres plateformes (switch.py, number.py, binary_sensor.py)
        # sur le même cycle, au lieu de les laisser gérer leur propre polling natif HA.
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
    def __init__(self, hass, config, handler, entry_id, model_label, enabled_default=True):
        self.hass = hass
        self._config = config
        self._handler = handler
        self._entry_id = entry_id
        self._model_label = model_label
        self._state = None
        self._active = False

        self._attr_translation_key = config.get("translation_key")
        self._attr_has_entity_name = True
        self._attr_icon = config.get("icon", "mdi:water")
        self._attr_native_unit_of_measurement = config.get("unit", "")
        self._attr_unique_id = config["unique_id"]
        # Ne s'applique qu'à la première création de l'entité : une entité déjà
        # présente chez l'utilisateur garde son état activé/désactivé actuel.
        self._attr_entity_registry_enabled_default = enabled_default
        # Le rafraîchissement est piloté par le controller (async_track_time_interval),
        # pas par le mécanisme de polling natif de HA : pas besoin que HA nous appelle aussi.
        self._attr_should_poll = False

        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")
        if config.get("entity_category") == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_active(self) -> bool:
        return self._active

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
        self._active = True
        last_state = await self.async_get_last_state()
        if last_state and self._state is None:
            try:
                self._state = float(last_state.state)
            except ValueError:
                pass

    async def async_will_remove_from_hass(self):
        self._active = False

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
