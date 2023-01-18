import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback

from .constants import DOMAIN, CONF_PATH, CONF_CHECK_CODE, CONF_CLIENT_ID, CONF_CLIENT_SECRET, URL_GET_CODE, \
    CONF_ADD_TOKEN, CONF_MAX_REMOTE_FILE, DEFAULT_MAX_REMOTE_FILE
from .yad import async_get_token

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({(CONF_PATH): str})

SECURITY_KEYS = [CONF_ADD_TOKEN, CONF_CHECK_CODE]
INTEGRATION_TITLE = 'Backup to YandexDisk'
PLACEHOLDER_CHECK_CODE_URL = 'check_code_url'


def option_without_secret_data(options: dict) -> dict:
    result = {}
    for key, value in options.items():
        if key not in SECURITY_KEYS:
            result[key] = value

    return result


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _data = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data = user_input
            return await self.async_step_client()

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_PATH): cv.string,
                vol.Required(CONF_MAX_REMOTE_FILE, default=DEFAULT_MAX_REMOTE_FILE): cv.positive_int
            })
        )

    async def async_step_client(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_token()

        return self.async_show_form(
            step_id='client',
            data_schema=vol.Schema({
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

            return self.async_create_entry(title=INTEGRATION_TITLE, data=option_without_secret_data(self._data))

        url = URL_GET_CODE + self._data[CONF_CLIENT_ID]
        return self.async_show_form(
            step_id='token',
            data_schema=vol.Schema({
                vol.Required(CONF_CHECK_CODE): cv.string
            }),
            description_placeholders={PLACEHOLDER_CHECK_CODE_URL: url}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    _data = {}

    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        self._data.update(self.config_entry.options)
        path = self._data[CONF_PATH]
        max_remote_file = self._data.setdefault(CONF_MAX_REMOTE_FILE, DEFAULT_MAX_REMOTE_FILE)

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required(CONF_PATH, default=path): cv.string,
                vol.Required(CONF_MAX_REMOTE_FILE, default=max_remote_file): cv.positive_int,
                vol.Required(CONF_ADD_TOKEN, default=False): cv.boolean
            })
        )

    async def async_step_user(self, user_input: dict = None):
        if user_input[CONF_ADD_TOKEN]:
            self._data = user_input
            return await self.async_step_client()
        self._data.update(user_input)
        return self.async_create_entry(title='', data=option_without_secret_data(self._data))

    async def async_step_client(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_token()

        return self.async_show_form(
            step_id='client',
            data_schema=vol.Schema({
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

            return self.async_create_entry(title='', data=option_without_secret_data(self._data))

        url = URL_GET_CODE + self._data[CONF_CLIENT_ID]
        return self.async_show_form(
            step_id='token',
            data_schema=vol.Schema({
                vol.Required(CONF_CHECK_CODE): cv.string
            }),
            description_placeholders={PLACEHOLDER_CHECK_CODE_URL: url}
        )
