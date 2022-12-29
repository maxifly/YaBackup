import base64
import logging

import requests
import yadisk as yadisk
from homeassistant.core import HomeAssistant

from .constants import CONF_PATH, HEAD_CONTENT_TYPE, CONTENT_TYPE_FORM, HEAD_AUTHORIZATION, URL_GET_TOKEN, CONF_TOKEN, \
    YANDEX_FIELD_ACCESS_TOKEN, YANDEX_FIELD_REFRESH_TOKEN, CONF_REFRESH_TOKEN, REST_TIMEOUT_SEC, HTTP_OK

_LOGGER = logging.getLogger(__name__)


async def async_get_token(hass: HomeAssistant, client_id, client_secret, check_code) -> dict:
    response = await  hass.async_add_executor_job(_get_token, client_id, client_secret, check_code)
    return response


def _get_token(client_id, client_secret, check_code) -> dict:
    headers = {}
    headers[HEAD_CONTENT_TYPE] = CONTENT_TYPE_FORM
    headers[HEAD_AUTHORIZATION] = 'Basic ' + str(
        _get_auth_string(client_id, client_secret))

    try:
        response = requests.post(URL_GET_TOKEN, headers=headers,
                                 data='grant_type=authorization_code&code=' + check_code,
                                 timeout=REST_TIMEOUT_SEC)
        if response.status_code != HTTP_OK:
            _LOGGER.error("Status code %s", response.status_code)
            _LOGGER.error("Request token result %s", response.status_code)
            raise ValueError

        json_response = response.json()

        result = {CONF_TOKEN: json_response[YANDEX_FIELD_ACCESS_TOKEN],
                  CONF_REFRESH_TOKEN: json_response[YANDEX_FIELD_REFRESH_TOKEN]}

        return result
    except Exception as e:
        _LOGGER.error("Error when get token", exc_info=True)
        raise e


def _get_auth_string(client_id, client_secret):
    return base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')


class YaDsk:
    _token = None
    _path = None
    _file_amount = 0

    @property
    def file_amount(self):
        return self._file_amount

    def __init__(self, hass: HomeAssistant, config: dict, unique_id=None):
        self._token = 'y0_AgAAAABKKZKkAAjy3gAAAADX4p7jeWCmi6ScS7Sg4LRY864tReTAkiM'
        self._path = config[CONF_PATH]
        self._hass = hass

    def get_info(self):
        return "path: " + self._path

    def update_config(self, config: dict):
        self._path = config[CONF_PATH]

        _LOGGER.info("Config updated to %s", self.get_info())

    # async def async_count_files(self):
    #     await self.count_files()

    async def count_files(self):
        await self._hass.async_add_executor_job(self._count_files)
        _LOGGER.debug("Count files result: %s", self.file_amount)

    def _count_files(self):
        try:
            y = yadisk.YaDisk(token=self._token)
            ll = list(y.listdir(self._path))
            self._file_amount = len(ll)
            _LOGGER.debug("-0- Count files result: %s", self.file_amount)
        except Exception as e:
            _LOGGER.error("Error get directory info. Path: %s", self._path, exc_info=True)
