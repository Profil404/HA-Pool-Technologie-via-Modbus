import asyncio
import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .models import MODELS

_LOGGER = logging.getLogger(__name__)

_BOOST_DURATION_REG = 4188
_BOOST_FLAG_REG = 4182
_BOOST_DURATION_MINUTES = 1440  # 24h

_PH_AUTO_REG = 4200

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    model_label = MODELS[config_entry.data["model"]]["name"]
    handler = controller.handler

    async_add_entities([
        BoostSwitch(hass, handler, controller, config_entry.entry_id, model_label),
        PHAutoSwitch(hass, handler, controller, config_entry.entry_id, model_label),
    ])

class BoostSwitch(SwitchEntity):
    def __init__(self, hass, handler, controller, entry_id, model_label):
        self._hass = hass
        self._handler = handler
        self._controller = controller
        self._entry_id = entry_id
        self._model_label = model_label

        self._attr_has_entity_name = True
        self._attr_translation_key = "boost"
        self._attr_icon = "mdi:rocket-launch"
        self._attr_unique_id = f"{entry_id}_boost"
        self._attr_is_on = False
        # Le rafraîchissement est piloté par le controller (même cycle que sensor.py),
        # pas par le mécanisme de polling natif de HA : pas besoin que HA nous appelle aussi.
        self._attr_should_poll = False

    @property
    def extra_state_attributes(self):
        return {"modbus_address": _BOOST_DURATION_REG, "modbus_flag_address": _BOOST_FLAG_REG}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }

    async def async_added_to_hass(self):
        await self._async_poll_refresh()
        self._controller.add_poll_listener(self._async_poll_refresh)

    async def async_will_remove_from_hass(self):
        self._controller.remove_poll_listener(self._async_poll_refresh)

    async def _async_poll_refresh(self) -> bool:
        result = await self._hass.async_add_executor_job(
            self._handler.read_register, _BOOST_DURATION_REG
        )
        if result is None:
            return False
        self._attr_is_on = result[0] > 0
        self.async_write_ha_state()
        return True

    async def async_turn_on(self, **kwargs):
        ok = await self._hass.async_add_executor_job(
            self._handler.write_register, _BOOST_DURATION_REG, _BOOST_DURATION_MINUTES
        )
        if not ok:
            _LOGGER.warning("Échec d'écriture de la durée du mode boost")
            return

        ok = await self._hass.async_add_executor_job(
            self._handler.write_register, _BOOST_FLAG_REG, 256
        )
        if not ok:
            _LOGGER.warning("Échec d'écriture du drapeau du mode boost")
            return

        await asyncio.sleep(0.5)
        verified = await self._hass.async_add_executor_job(
            self._handler.read_register_verified, _BOOST_DURATION_REG, _BOOST_DURATION_MINUTES
        )
        if not verified:
            _LOGGER.warning("Activation du mode boost non confirmée par l'appareil")
            return

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        ok = await self._hass.async_add_executor_job(
            self._handler.write_register, _BOOST_DURATION_REG, 0
        )
        if not ok:
            _LOGGER.warning("Échec de la désactivation du mode boost")
            return

        await asyncio.sleep(0.5)
        verified = await self._hass.async_add_executor_job(
            self._handler.read_register_verified, _BOOST_DURATION_REG, 0
        )
        if not verified:
            _LOGGER.warning("Désactivation du mode boost non confirmée par l'appareil")
            return

        self._attr_is_on = False
        self.async_write_ha_state()


class PHAutoSwitch(SwitchEntity):
    def __init__(self, hass, handler, controller, entry_id, model_label):
        self._hass = hass
        self._handler = handler
        self._controller = controller
        self._entry_id = entry_id
        self._model_label = model_label

        self._attr_has_entity_name = True
        self._attr_translation_key = "ph_auto"
        self._attr_icon = "mdi:tune"
        self._attr_unique_id = f"{entry_id}_ph_auto"
        self._attr_is_on = False
        self._attr_should_poll = False

    @property
    def extra_state_attributes(self):
        return {"modbus_address": _PH_AUTO_REG}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }

    async def async_added_to_hass(self):
        await self._async_poll_refresh()
        self._controller.add_poll_listener(self._async_poll_refresh)

    async def async_will_remove_from_hass(self):
        self._controller.remove_poll_listener(self._async_poll_refresh)

    async def _async_poll_refresh(self) -> bool:
        result = await self._hass.async_add_executor_job(
            self._handler.read_register, _PH_AUTO_REG
        )
        if result is None:
            return False
        self._attr_is_on = result[0] > 0
        self.async_write_ha_state()
        return True

    async def async_turn_on(self, **kwargs):
        ok = await self._hass.async_add_executor_job(
            self._handler.write_register, _PH_AUTO_REG, 1
        )
        if not ok:
            _LOGGER.warning("Échec d'activation de la régulation pH automatique")
            return

        await asyncio.sleep(0.5)
        verified = await self._hass.async_add_executor_job(
            self._handler.read_register_verified, _PH_AUTO_REG, 1
        )
        if not verified:
            _LOGGER.warning("Activation de la régulation pH automatique non confirmée par l'appareil")
            return

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        ok = await self._hass.async_add_executor_job(
            self._handler.write_register, _PH_AUTO_REG, 0
        )
        if not ok:
            _LOGGER.warning("Échec de la désactivation de la régulation pH automatique")
            return

        await asyncio.sleep(0.5)
        verified = await self._hass.async_add_executor_job(
            self._handler.read_register_verified, _PH_AUTO_REG, 0
        )
        if not verified:
            _LOGGER.warning("Désactivation de la régulation pH automatique non confirmée par l'appareil")
            return

        self._attr_is_on = False
        self.async_write_ha_state()
