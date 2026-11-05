import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity
from modbus_connection import ModbusError

from .entity import PoolTechnologieEntity
from .models import entity_status
from .options_helper import has_ph_probe
from .pool_technologie_modbus import WriteNotConfirmedError

_LOGGER = logging.getLogger(__name__)


class PoolSwitch(PoolTechnologieEntity, SwitchEntity, RestoreEntity):
    """Interrupteur qui reprend son dernier état connu au démarrage."""

    @property
    def _device_is_on(self) -> bool | None:
        """L'état lu sur l'appareil, ou None tant qu'il n'a pas été lu."""
        raise NotImplementedError

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        # Appareil éteint au démarrage : on affiche le dernier état connu plutôt
        # que « désactivé », jusqu'à la première lecture réussie.
        if self._device_is_on is not None:
            return
        last_state = await self.async_get_last_state()
        if last_state and last_state.state in (STATE_ON, STATE_OFF):
            self._attr_is_on = last_state.state == STATE_ON

    @callback
    def _handle_coordinator_update(self):
        if (active := self._device_is_on) is not None:
            self._attr_is_on = active
        super()._handle_coordinator_update()


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = config_entry.runtime_data
    model_key = config_entry.data["model"]

    entities = []
    create, enabled_default = entity_status("boost_remaining", model_key)
    if create:
        entities.append(BoostSwitch(coordinator, enabled_default))
    # Sans sonde pH, la régulation pH automatique n'a pas de sens
    create, enabled_default = entity_status("ph_regulation", model_key)
    if create and has_ph_probe(config_entry):
        entities.append(PHAutoSwitch(coordinator, enabled_default))
    async_add_entities(entities)


class BoostSwitch(PoolSwitch):
    def __init__(self, coordinator, enabled_default=True):
        super().__init__(coordinator, "boost_remaining")

        self._attr_translation_key = "boost"
        self._attr_icon = "mdi:rocket-launch"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_boost"
        self._attr_is_on = False
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def extra_state_attributes(self):
        device = self.coordinator.device
        return {
            "modbus_address": device.address("boost_remaining"),
            "modbus_flag_address": device.address("boost_flag"),
        }

    @property
    def _device_is_on(self):
        return self.coordinator.device.boost_active

    async def async_turn_on(self, **kwargs):
        try:
            await self.coordinator.device.async_set_boost(True)
        except WriteNotConfirmedError:
            _LOGGER.warning("Activation du mode boost non confirmée par l'appareil")
            return
        except ModbusError as err:
            _LOGGER.warning("Échec d'écriture du mode boost : %s", err)
            return

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        try:
            await self.coordinator.device.async_set_boost(False)
        except WriteNotConfirmedError:
            _LOGGER.warning("Désactivation du mode boost non confirmée par l'appareil")
            return
        except ModbusError as err:
            _LOGGER.warning("Échec de la désactivation du mode boost : %s", err)
            return

        self._attr_is_on = False
        self.async_write_ha_state()


class PHAutoSwitch(PoolSwitch):
    def __init__(self, coordinator, enabled_default=True):
        super().__init__(coordinator, "ph_regulation")

        self._attr_translation_key = "ph_auto"
        self._attr_icon = "mdi:tune"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_ph_auto"
        self._attr_is_on = False
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def _device_is_on(self):
        return self.coordinator.device.ph_regulation_active

    async def async_turn_on(self, **kwargs):
        try:
            await self.coordinator.device.async_set_ph_regulation(True)
        except WriteNotConfirmedError:
            _LOGGER.warning(
                "Activation de la régulation pH automatique non confirmée par l'appareil"
            )
            return
        except ModbusError as err:
            _LOGGER.warning("Échec d'activation de la régulation pH automatique : %s", err)
            return

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        try:
            await self.coordinator.device.async_set_ph_regulation(False)
        except WriteNotConfirmedError:
            _LOGGER.warning(
                "Désactivation de la régulation pH automatique non confirmée par l'appareil"
            )
            return
        except ModbusError as err:
            _LOGGER.warning("Échec de la désactivation de la régulation pH automatique : %s", err)
            return

        self._attr_is_on = False
        self.async_write_ha_state()
