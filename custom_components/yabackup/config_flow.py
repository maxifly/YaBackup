import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback

from .constants import DOMAIN, CONF_PATH

DATA_SCHEMA = vol.Schema({(CONF_PATH): str})


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title='Test PMU', data=user_input)

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_PATH): cv.string
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        path = self.config_entry.options[CONF_PATH]


        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_PATH, default=path): cv.string
            })
        )

    async def async_step_user(self, user_input: dict = None):
        return self.async_create_entry(title='', data=user_input)
