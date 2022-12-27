import logging

from .constants import CONF_PATH

_LOGGER = logging.getLogger(__name__)


class YaDsk:
    _token = None
    _path = None

    def __init__(self, config: dict, unique_id=None):
        self._token = 'y0_AgAAAABKKZKkAAjy3gAAAADX4p7jeWCmi6ScS7Sg4LRY864tReTAkiM'
        self._path = config[CONF_PATH]

    def get_info(self):
        return "path: " + self._path

    def update_config(self, config: dict):
        self._path = config[CONF_PATH]

        _LOGGER.info("Config updated to " + self.get_info())

    def count_files(self):
        # y = yadisk.YaDisk(token=self._token)
        # ll = list(y.listdir(self._path))
        return 125
