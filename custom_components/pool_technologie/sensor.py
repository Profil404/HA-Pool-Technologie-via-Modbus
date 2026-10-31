from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import PoolTechnologieEntity
from .models import SENSORS, PH_SENSOR_KEYS, ORP_SENSOR_KEYS, entity_status
from .options_helper import has_ph_probe, has_orp_probe


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = config_entry.runtime_data
    model_key = config_entry.data["model"]

    ph_probe = has_ph_probe(config_entry)
    orp_probe = has_orp_probe(config_entry)

    sensors = []
    for sensor_conf in SENSORS:
        key = sensor_conf["translation_key"]
        if key in PH_SENSOR_KEYS and not ph_probe:
            continue
        if key in ORP_SENSOR_KEYS and not orp_probe:
            continue
        create, enabled_default = entity_status(sensor_conf["field"], model_key)
        if not create:
            continue
        sensors.append(PoolSensor(coordinator, sensor_conf, enabled_default))

    async_add_entities(sensors)


class PoolSensor(PoolTechnologieEntity, SensorEntity, RestoreEntity):
    def __init__(self, coordinator, config, enabled_default=True):
        super().__init__(coordinator, config["field"])
        self._state = None

        self._attr_translation_key = config["translation_key"]
        self._attr_icon = config.get("icon", "mdi:water")
        self._attr_native_unit_of_measurement = coordinator.device.field(config["field"]).unit or ""
        self._attr_unique_id = config["unique_id"]
        # Ne s'applique qu'à la première création de l'entité : une entité déjà
        # présente chez l'utilisateur garde son état activé/désactivé actuel.
        self._attr_entity_registry_enabled_default = enabled_default

        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")
        if config.get("entity_category") == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    # L'état publié est la valeur lue telle quelle, comme avant la migration.
    @property  # type: ignore[misc]
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and self._state is None:
            try:
                self._state = float(last_state.state)
            except ValueError:
                pass

    @callback
    def _handle_coordinator_update(self):
        # Lecture hors plage ou en échec : on garde la dernière valeur connue
        # plutôt que d'afficher n'importe quoi.
        if (value := self._value) is not None:
            self._state = value
        super()._handle_coordinator_update()
