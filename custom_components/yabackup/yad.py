import base64
import datetime
import logging
from typing import Generator

import requests
import yadisk as yadisk
from homeassistant.components.backup import BackupManager
from homeassistant.components.backup.const import DOMAIN as BACKUP_DOMAIN
from homeassistant.core import HomeAssistant
from yadisk.objects import ResourceObject
from yadisk.objects import TokenObject

from .constants import CONF_PATH, HEAD_CONTENT_TYPE, CONTENT_TYPE_FORM, HEAD_AUTHORIZATION, URL_GET_TOKEN, CONF_TOKEN, \
    YANDEX_FIELD_ACCESS_TOKEN, YANDEX_FIELD_REFRESH_TOKEN, CONF_REFRESH_TOKEN, REST_TIMEOUT_SEC, HTTP_OK, \
    CONF_MAX_REMOTE_FILE, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_TOKEN_EXPIRES

_LOGGER = logging.getLogger(__name__)

TYPE_FILE = 'file'


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


def _refresh_token_request(refresh_token, client_id, client_secret):
    try:
        _LOGGER.debug("Try refresh token")
        token_object: TokenObject = yadisk.functions.refresh_token(refresh_token, client_id, client_secret)

        return {CONF_TOKEN: token_object['access_token'],
                CONF_REFRESH_TOKEN: token_object['refresh_token'],
                CONF_TOKEN_EXPIRES: token_object['expires_in']}

    except Exception as e:
        _LOGGER.error("Error when refresh token", exc_info=True)
        raise e


def _get_auth_string(client_id, client_secret):
    return base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')


class YaDsk:
    _token = None
    _path = None
    _upload_without_suffix = True
    _max_remote_file_amount = 5
    _file_amount = 0
    _file_markdown_list = ""
    _file_list = []
    _update_listeners = []

    @property
    def file_amount(self):
        return self._file_amount

    @property
    def file_markdown_list(self):
        return self._file_markdown_list

    def __init__(self, hass: HomeAssistant, config: dict, unique_id=None):
        self._options = {}
        self._options.update(config)
        self._token = config[CONF_TOKEN]
        self._refresh_token_value = config[CONF_REFRESH_TOKEN]
        self._token_expire_in = config.get(CONF_TOKEN_EXPIRES, 0)
        self._path = config[CONF_PATH]
        self._max_remote_file_amount = config[CONF_MAX_REMOTE_FILE]
        self._client_id = config[CONF_CLIENT_ID]
        self._client_s = config[CONF_CLIENT_SECRET]
        self._hass = hass

    def get_info(self):
        return "path: " + self._path

    def update_config(self, config: dict):
        self._options = {}
        self._options.update(config)
        self._path = config[CONF_PATH]
        self._max_remote_file_amount = config[CONF_MAX_REMOTE_FILE]
        self._token = config[CONF_TOKEN]
        self._refresh_token_value = config[CONF_REFRESH_TOKEN]
        self._token_expire_in = config.get(CONF_TOKEN_EXPIRES, 0)
        self._client_id = config[CONF_CLIENT_ID]
        self._client_s = config[CONF_CLIENT_SECRET]

        _LOGGER.info("Config updated to %s", self.get_info())

    def add_update_listener(self, coro):
        """Listeners to handle automatic data update."""
        self._update_listeners.append(coro)

    async def count_files(self):
        await self._hass.async_add_executor_job(self._count_files)
        _LOGGER.debug("Count files result: %s", self.file_amount)

    def _count_files(self):
        try:
            y = yadisk.YaDisk(token=self._token)
            files = self._file_list_processing(y.listdir(self._path))
            self._file_amount = len(files)
            self._file_markdown_list = self._get_markdown_files(files, 10)
            self._file_list = [file.name for file in files]
            _LOGGER.debug("Count files result: %s", self.file_amount)
        except Exception as e:
            _LOGGER.error("Error get directory info. Path: %s", self._path, exc_info=True)

    async def upload_files(self):
        await self._refresh_token()

        local_backups = await self.get_local_files_list()
        await self.count_files()

        new_files = [file for file in local_backups.keys() if file not in self._file_list]

        _LOGGER.info("Need backup %d files", len(new_files))

        y = yadisk.YaDisk(token=self._token)
        for file in new_files:
            await self._hass.async_add_executor_job(self._upload_file,
                                                    y, str(local_backups[file]), self._path + '/' + file)
        is_deleted = False
        # Delete files from remote directory
        if (self._file_amount + len(new_files)) > self._max_remote_file_amount:
            is_deleted = True
            old_file_count = (self._file_amount + len(new_files)) - self._max_remote_file_amount
            if old_file_count > self._file_amount:
                old_file_count = self._file_amount

            _LOGGER.debug("Need delete %d files", old_file_count)

            old_files = self._file_list[-old_file_count:]

            for old_file in old_files:
                await self._hass.async_add_executor_job(self._remove_file,
                                                        y, self._path + '/' + old_file)

        if new_files or is_deleted:
            await self.count_files()

    async def get_local_files_list(self):

        manager: BackupManager = self._hass.data[BACKUP_DOMAIN]
        backups = await manager.get_backups()

        result = {}
        for backup in backups.values():
            key = backup.name + '_' + backup.slug
            if not self._upload_without_suffix:
                key += '.tar'
            result[key] = backup.path

        return result

    def _upload_file(self, y: yadisk.YaDisk, source_file, destination_file):
        try:
            _LOGGER.info('Upload file %s to %s', source_file, destination_file)
            y.upload(source_file, destination_file, overwrite=True, n_retries=3, retry_interval=5,
                     timeout=(15.0, 250.0))
            _LOGGER.info('File %s uploaded to %s', source_file, destination_file)
        except Exception as e:
            _LOGGER.error("Error upload file %s", source_file, exc_info=True)
            raise e

    def _remove_file(self, y: yadisk.YaDisk, deleted_file):
        try:
            _LOGGER.info('Remove file %s', deleted_file)
            y.remove(deleted_file, n_retries=3, retry_interval=5)
            _LOGGER.info('File %s removed', deleted_file)
        except Exception as e:
            _LOGGER.error("Error when remove file %s", deleted_file, exc_info=True)
            raise e

    def _get_local_backup_dir(self):
        return self._hass.data[BACKUP_DOMAIN].backup_dir

    async def _refresh_token(self):
        result = await self._hass.async_add_executor_job(_refresh_token_request, self._refresh_token_value,
                                                         self._client_id, self._client_s)

        self._refresh_token_value = result[CONF_REFRESH_TOKEN]
        self._token = result[CONF_TOKEN]
        self._token_expire_in = result[CONF_TOKEN_EXPIRES]
        self._options.update(result)

        await self._handle_update()

    async def _handle_update(self):
        self._options['wwww'] = datetime.datetime.now()
        for coro in self._update_listeners:
            await coro(
                self._options
            )

    @staticmethod
    def _file_list_processing(objects: Generator[any, any, ResourceObject]) -> list:
        files = [obj for obj in objects if obj.type == TYPE_FILE]
        result = sorted(files, key=lambda obj: obj.modified, reverse=True)
        return result

    @staticmethod
    def _get_markdown_files(files: list[ResourceObject], max_items: int):
        if len(files) == 0:
            return ""

        result = "|name|modification|\n|---|---|"
        file_count = 0
        for file in files:
            result += "\n|{0:s}|{1}|".format(file.name, file.modified)
            file_count += 1
            if file_count >= max_items:
                break
        return result
