import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_ID,
    CONF_MODEL,
    CONF_REGULATION_ORP,
    CONF_SCAN_INTERVAL,
    SCAN_INTERVAL,
)
from .models import MODELS

class PoolTechnologieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            model_name = MODELS[user_input[CONF_MODEL]]["name"]
            return self.async_create_entry(
                title=model_name,
                data={
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_UNIT_ID: user_input[CONF_UNIT_ID],
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_REGULATION_ORP: user_input[CONF_REGULATION_ORP],
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                }
            )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=502): int,
            vol.Required(CONF_UNIT_ID, default=1): int,
            vol.Required(CONF_MODEL): vol.In({k: v["name"] for k, v in MODELS.items()}),
            vol.Required(CONF_REGULATION_ORP, default=False): bool,
            vol.Required(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

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
