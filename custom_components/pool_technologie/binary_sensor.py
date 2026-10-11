from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from .const import DOMAIN
from .models import CELL_DIAGNOSTICS_CONFIRMED, CELL_DIAGNOSTICS_UNSUPPORTED, MODELS

# Alarmes de l'électrolyseur, lues sur le registre 4172 (bitmask), d'après l'issue #4
# (électrolyseur RACER, même plateforme Modbus). Bits non confirmés sur les autres modèles.
_REG_ALARMS = 4172

_CELL_ALARMS = (
    {
        "translation_key": "alarme_defaut_cellule",
        "unique_id": "alarme_defaut_cellule",
        "bitmask": 0x0002,
        "icon": "mdi:alert-circle",
    },
    {
        "translation_key": "alarme_manque_sel",
        "unique_id": "alarme_manque_sel",
        "bitmask": 0x0004,
        "icon": "mdi:shaker-outline",
    },
    {
        "translation_key": "alarme_trop_sel",
        "unique_id": "alarme_trop_sel",
        "bitmask": 0x0008,
        "icon": "mdi:shaker-outline",
    },
    {
        "translation_key": "alarme_eau_froide",
        "unique_id": "alarme_eau_froide",
        "bitmask": 0x0010,
        "icon": "mdi:snowflake-alert",
    },
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    model_key = config_entry.data["model"]
    model_label = MODELS[model_key]["name"]
    handler = controller.handler
    entry_id = config_entry.entry_id

    entities = [ModbusStatusSensor(entry_id, model_label, controller)]

    # Diagnostics cellule (alarmes) : l'iBasel Duo ne remonte pas ces registres.
    if model_key not in CELL_DIAGNOSTICS_UNSUPPORTED:
        enabled_default = model_key in CELL_DIAGNOSTICS_CONFIRMED
        group = CellAlarmGroup(hass, handler, controller)
        for alarm in _CELL_ALARMS:
            entity = CellAlarmBinarySensor(entry_id, model_label, alarm, enabled_default)
            group.add(entity)
            entities.append(entity)
        await group.start()

    async_add_entities(entities)


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


class CellAlarmBinarySensor(BinarySensorEntity):
    """Une alarme de l'électrolyseur, dérivée d'un bit du registre 4172."""

    _attr_should_poll = False

    def __init__(self, entry_id, model_label, config, enabled_default):
        self._entry_id = entry_id
        self._model_label = model_label
        self._bitmask = config["bitmask"]

        self._attr_has_entity_name = True
        self._attr_translation_key = config["translation_key"]
        self._attr_unique_id = f"{entry_id}_{config['unique_id']}"
        self._attr_icon = config["icon"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        # Entité désactivée par défaut sur les modèles non confirmés (cf. models.py).
        self._attr_entity_registry_enabled_default = enabled_default
        self._attr_is_on = False

    def apply(self, raw):
        """Met à jour l'état depuis la valeur brute du registre 4172 (appelé par CellAlarmGroup)."""
        self._attr_is_on = bool(raw & self._bitmask)

    @property
    def is_on(self):
        return self._attr_is_on

    @property
    def extra_state_attributes(self):
        return {"modbus_address": _REG_ALARMS}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }


class CellAlarmGroup:
    """Lit le registre 4172 une seule fois par cycle et répartit les bits.

    Les quatre alarmes partagent la même lecture : au lieu de quatre lectures du
    même registre à chaque cycle, une seule lecture alimente les quatre entités.
    """

    def __init__(self, hass, handler, controller):
        self._hass = hass
        self._handler = handler
        self._controller = controller
        self._sensors = []

    def add(self, sensor):
        self._sensors.append(sensor)

    async def start(self):
        await self.refresh()
        self._controller.add_poll_listener(self.refresh)

    async def refresh(self) -> bool:
        result = await self._hass.async_add_executor_job(
            self._handler.read_register, _REG_ALARMS
        )
        if result is None:
            return False
        raw = int(result[0])
        for sensor in self._sensors:
            sensor.apply(raw)
            sensor.async_write_ha_state()
        return True
