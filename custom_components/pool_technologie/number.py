import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfElectricPotential
from homeassistant.core import callback
from modbus_connection import ModbusError

from .entity import PoolTechnologieEntity
from .models import entity_status
from .options_helper import has_ph_probe, has_orp_probe
from .pool_technologie_modbus import WriteNotConfirmedError

_LOGGER = logging.getLogger(__name__)

# Réglages modifiables, dans l'ordre de création. "written" donne la valeur
# affichée après une écriture confirmée, à partir de la valeur demandée.
NUMBERS = {
    "consigne_ph": {
        "field": "ph_setpoint",
        "icon": "mdi:cog",
        "unit": "pH",
        "initial": 7.2,
        "step": 0.1,
        "written": lambda value: value,
        "write_failed": "Échec d'écriture de la consigne pH (raw=%s)",
        "not_confirmed": "Consigne pH non confirmée par l'appareil après écriture (raw=%s)",
    },
    "consigne_orp": {
        "field": "orp_setpoint",
        "icon": "mdi:cog",
        "unit": UnitOfElectricPotential.MILLIVOLT,
        "initial": 650,
        "step": 10,
        "written": int,
        "write_failed": "Échec d'écriture de la consigne ORP (%s)",
        "not_confirmed": "Consigne ORP non confirmée par l'appareil après écriture (%s)",
    },
    "consigne_electrolyse": {
        "field": "electrolysis_setpoint",
        "icon": "mdi:cog",
        "unit": "%",
        "initial": 20,
        "step": 1,
        "written": int,
        "write_failed": "Échec d'écriture de la consigne électrolyse (%s)",
        "not_confirmed": "Consigne électrolyse non confirmée par l'appareil après écriture (%s)",
    },
    "concentration_correcteur_ph": {
        "field": "ph_corrector_concentration",
        "icon": "mdi:flask-outline",
        "unit": "%",
        "initial": 15,
        "step": 1,
        "written": lambda value: float(int(round(value))),
        "write_failed": "Échec d'écriture de la concentration correcteur pH (%s)",
        "not_confirmed": (
            "Concentration correcteur pH non confirmée par l'appareil après écriture (%s)"
        ),
    },
    "taille_bassin": {
        "field": "pool_volume",
        "icon": "mdi:texture-box",
        "unit": "m³",
        "initial": 30,
        "step": 1,
        "written": lambda value: int(round(value)),
        "write_failed": "Échec d'écriture de la taille du bassin (%s)",
        "not_confirmed": "Taille du bassin non confirmée par l'appareil après écriture (%s)",
    },
    "heure_inversion_cellule": {
        "field": "cell_inversion_interval",
        "icon": "mdi:swap-horizontal",
        "unit": "h",
        "initial": 4,
        "step": 1,
        "written": lambda value: int(round(value)),
        "write_failed": "Échec d'écriture de l'heure d'inversion cellule (%s)",
        "not_confirmed": (
            "Heure d'inversion cellule non confirmée par l'appareil après écriture (%s)"
        ),
    },
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = config_entry.runtime_data
    model_key = config_entry.data["model"]

    ph_probe = has_ph_probe(config_entry)
    regulation_orp = has_orp_probe(config_entry)
    wanted = {
        "consigne_ph": ph_probe,
        "consigne_orp": regulation_orp,
        # Consigne électrolyse : seulement en régulation manuelle, sans sonde ORP,
        # qui pilote sinon l'électrolyse automatiquement.
        "consigne_electrolyse": not regulation_orp,
        # Même mapping Modbus que Consigne pH, lié à la présence de la sonde pH.
        "concentration_correcteur_ph": ph_probe,
        "taille_bassin": True,
        "heure_inversion_cellule": True,
    }

    entities = []
    for key, description in NUMBERS.items():
        if not wanted[key]:
            continue
        # Non créée sur un modèle confirmé non fonctionnel, créée désactivée par
        # défaut sur un modèle non testé (cf. models.py).
        create, enabled_default = entity_status(description["field"], model_key)
        if create:
            entities.append(PoolNumber(coordinator, key, description, enabled_default))
    async_add_entities(entities)


class PoolNumber(PoolTechnologieEntity, NumberEntity):
    def __init__(self, coordinator, key, description, enabled_default=True):
        super().__init__(coordinator, description["field"])
        self._description = description
        valid = coordinator.device.field(description["field"]).valid

        self._attr_translation_key = key
        self._attr_entity_category = None
        self._attr_icon = description["icon"]
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = description["unit"]
        self._attr_mode = "box"
        self._attr_native_value = description["initial"]
        self._attr_native_min_value = valid[0]
        self._attr_native_max_value = valid[1]
        self._attr_native_step = description["step"]
        # Ne s'applique qu'à la première création de l'entité : une entité déjà présente
        # chez l'utilisateur garde son état activé/désactivé actuel.
        self._attr_entity_registry_enabled_default = enabled_default

    @callback
    def _handle_coordinator_update(self):
        # Valeur hors plage (appareil éteint ou lecture aberrante) : on ignore et on
        # garde la dernière valeur connue plutôt que d'afficher n'importe quoi.
        if (value := self._value) is not None:
            self._attr_native_value = value
        super()._handle_coordinator_update()

    async def async_set_native_value(self, value: float) -> None:
        device = self.coordinator.device
        field = self._description["field"]
        raw = device.field(field).to_raw(value)
        try:
            await device.async_write(field, value)
        except WriteNotConfirmedError:
            _LOGGER.warning(self._description["not_confirmed"], raw)
            return
        except ModbusError:
            _LOGGER.warning(self._description["write_failed"], raw)
            return

        self._attr_native_value = self._description["written"](value)
        self.async_write_ha_state()
