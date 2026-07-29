import asyncio
import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .models import MODELS

_LOGGER = logging.getLogger(__name__)

_BOOST_DURATION_REG = 4188
_BOOST_FLAG_REG = 4182
_BOOST_DURATION_MINUTES = 1440  # 24h

async def async_setup_entry(hass, config_entry, async_add_entities):
    controller = hass.data[DOMAIN][config_entry.entry_id]["controller"]
    model_label = MODELS[config_entry.data["model"]]["name"]
    handler = controller.handler

    async_add_entities([
        BoostSwitch(hass, handler, config_entry.entry_id, model_label)
    ])

class BoostSwitch(SwitchEntity):
    def __init__(self, hass, handler, entry_id, model_label):
        self._hass = hass
        self._handler = handler
        self._entry_id = entry_id
        self._model_label = model_label

        self._attr_has_entity_name = True
        self._attr_translation_key = "boost"
        self._attr_icon = "mdi:rocket-launch"
        self._attr_unique_id = f"{entry_id}_boost"
        self._attr_is_on = False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._model_label,
            "manufacturer": "Pool Technologie",
            "model": self._model_label,
        }

    async def async_update(self):
        result = await self._hass.async_add_executor_job(
            self._handler.read_register, _BOOST_DURATION_REG
        )
        if result is not None:
            self._attr_is_on = result[0] > 0

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
