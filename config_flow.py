import voluptuous as vol
from homeassistant import config_entries
from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_ID,
    CONF_MODEL,
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
                }
            )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=502): int,
            vol.Required(CONF_UNIT_ID, default=1): int,
            vol.Required(CONF_MODEL): vol.In({k: v["name"] for k, v in MODELS.items()}),
        })

        return self.async_show_form(step_id="user", data_schema=schema)
