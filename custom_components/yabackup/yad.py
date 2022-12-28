import logging

import yadisk as yadisk
from homeassistant.core import HomeAssistant

from .constants import CONF_PATH

_LOGGER = logging.getLogger(__name__)


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

        _LOGGER.info(f"Config updated to {self.get_info()}")

    # async def async_count_files(self):
    #     await self.count_files()

    async def count_files(self):
        await self._hass.async_add_executor_job(self._count_files)
        _LOGGER.debug(f"Count files result: {self.file_amount}")

    def _count_files(self):
        try:
            y = yadisk.YaDisk(token=self._token)
            ll = list(y.listdir(self._path))
            self._file_amount = len(ll)
            _LOGGER.debug(f"-0- Count files result: {self.file_amount}")
        except Exception as e:
            _LOGGER.error(f"Error get directory info. Path: {self._path}", exc_info = True)

