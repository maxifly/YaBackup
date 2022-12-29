import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback

from .constants import DOMAIN, CONF_PATH, CONF_CHECK_CODE, CONF_CLIENT_ID, CONF_CLIENT_SECRET, URL_GET_CODE
from .yad import async_get_token

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({(CONF_PATH): str})


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _data = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data = user_input
            return await self.async_step_token()

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_PATH): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string
            })
        )

    async def async_step_token(self, user_input=None):
        if user_input is not None:
            self._data[CONF_CHECK_CODE] = user_input[CONF_CHECK_CODE]
            token_info = await async_get_token(self.hass,
                                               self._data[CONF_CLIENT_ID],
                                               self._data[CONF_CLIENT_SECRET],
                                               self._data[CONF_CHECK_CODE])

            _LOGGER.debug(f"Get token: {token_info}")
            self._data.update(token_info)

            return self.async_create_entry(title='Test PMU', data=self._data)

        url = URL_GET_CODE + self._data[CONF_CLIENT_ID]
        return self.async_show_form(
            step_id='token',
            data_schema=vol.Schema({
                vol.Required("text", default=url): cv.string,
                vol.Required(CONF_CHECK_CODE): cv.string
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
