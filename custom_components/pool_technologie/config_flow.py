import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from modbus_connection import ModbusError, ModbusTcpParams
from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_ID,
    CONF_MODEL,
    CONF_REGULATION_ORP,
    CONF_SONDE_PH,
    CONF_SCAN_INTERVAL,
    SCAN_INTERVAL,
)
from .models import MODELS
from .pool_technologie_modbus import PoolTechnologieDevice


async def _async_validate(hass, host, port, unit_id):
    """Lit l'électrolyseur une fois, sur la connexion partagée de Home Assistant.

    Lève HomeAssistantError si la passerelle est déjà utilisée avec d'autres
    paramètres de liaison, ModbusError si l'électrolyseur ne répond pas.
    """
    params = ModbusTcpParams(host=host, port=port)
    async with async_get_temporary_unit(hass, params, unit_id) as unit:
        await PoolTechnologieDevice(unit).async_validate()


class PoolTechnologieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({
                CONF_HOST: user_input[CONF_HOST],
                CONF_PORT: user_input[CONF_PORT],
                CONF_UNIT_ID: user_input[CONF_UNIT_ID],
            })
            try:
                await _async_validate(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_UNIT_ID],
                )
            except HomeAssistantError:
                errors["base"] = "link_conflict"
            except ModbusError:
                errors["base"] = "cannot_connect"
            else:
                model_name = MODELS[user_input[CONF_MODEL]]["name"]
                return self.async_create_entry(
                    title=model_name,
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_UNIT_ID: user_input[CONF_UNIT_ID],
                        CONF_MODEL: user_input[CONF_MODEL],
                        CONF_SONDE_PH: user_input[CONF_SONDE_PH],
                        CONF_REGULATION_ORP: user_input[CONF_REGULATION_ORP],
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    }
                )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=502): vol.All(int, vol.Range(min=1, max=65535)),
            vol.Required(CONF_UNIT_ID, default=1): vol.All(int, vol.Range(min=0, max=255)),
            vol.Required(CONF_MODEL): vol.In({k: v["name"] for k, v in MODELS.items()}),
            vol.Required(CONF_SONDE_PH, default=True): bool,
            vol.Required(CONF_REGULATION_ORP, default=False): bool,
            vol.Required(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PoolTechnologieOptionsFlow()


class PoolTechnologieOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self.config_entry
        schema = vol.Schema({
            vol.Required(
                CONF_SONDE_PH,
                default=entry.options.get(
                    CONF_SONDE_PH, entry.data.get(CONF_SONDE_PH, True)
                ),
            ): bool,
            vol.Required(
                CONF_REGULATION_ORP,
                default=entry.options.get(
                    CONF_REGULATION_ORP, entry.data.get(CONF_REGULATION_ORP, False)
                ),
            ): bool,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=entry.options.get(
                    CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
                ),
            ): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
