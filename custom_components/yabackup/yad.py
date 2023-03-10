""" Core integration objects"""
import base64
import datetime
import json
import logging
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import requests
import yadisk as yadisk
from homeassistant.core import HomeAssistant
from yadisk.objects import ResourceObject
from yadisk.objects import TokenObject

from .constants import CONF_PATH, HEAD_CONTENT_TYPE, CONTENT_TYPE_FORM, HEAD_AUTHORIZATION, URL_GET_TOKEN, CONF_TOKEN, \
    YANDEX_FIELD_ACCESS_TOKEN, YANDEX_FIELD_REFRESH_TOKEN, CONF_REFRESH_TOKEN, REST_TIMEOUT_SEC, HTTP_OK, \
    CONF_MAX_REMOTE_FILE, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_TOKEN_EXPIRES, REFRESH_TOKEN_DELTA

_LOGGER = logging.getLogger(__name__)

TYPE_FILE = 'file'


async def async_get_token(hass: HomeAssistant, client_id, client_secret, check_code) -> dict:
    """ Get token. Async call from hass core."""
    response = await  hass.async_add_executor_job(_get_token, client_id, client_secret, check_code)
    return response


def _get_token(client_id, client_secret, check_code) -> dict:
    """ Get token. """
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
    """ Refresh token. """
    try:
        _LOGGER.debug("Try refresh token")
        token_object: TokenObject = yadisk.functions.refresh_token(refresh_token, client_id, client_secret)

        expire_seconds = token_object['expires_in']
        expire_data = datetime.datetime.now() + datetime.timedelta(seconds=expire_seconds)
        _LOGGER.debug("New token expires in %s", expire_data)

        return {CONF_TOKEN: token_object['access_token'],
                CONF_REFRESH_TOKEN: token_object['refresh_token'],
                CONF_TOKEN_EXPIRES: expire_data.isoformat()}

    except Exception as e:
        _LOGGER.error("Error when refresh token", exc_info=True)
        raise e


def _get_auth_string(client_id, client_secret):
    """ Get auth string for basic authorisation """
    return base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')


@dataclass
class Backup:
    """Backup class."""

    slug: str
    name: str
    date: str
    path: Path
    size: float


class BackupObserver:
    """Backup observer.
    Base on core BackupManager
    """

    def __init__(self, hass: HomeAssistant, backup_dir: str) -> None:
        """ Initialize the backup observer."""
        self.hass = hass
        self.backup_dir = Path(hass.config.path("backups")) if backup_dir is None else Path(backup_dir)

    async def get_backups(self) -> dict[str, Backup]:
        """ Get data of stored backup files."""
        backups = await self.hass.async_add_executor_job(self._read_backups)

        _LOGGER.debug("Loaded %s backups", len(backups))

        return backups

    def _read_backups(self) -> dict[str, Backup]:
        """Read backups from disk."""
        _LOGGER.debug("Check %s path", self.backup_dir)

        _LOGGER.debug("Size %s", len(list(self.backup_dir.glob("*"))))

        for backup_path in self.backup_dir.glob("*"):
            _LOGGER.debug("backup_path %s", backup_path)

        backups: dict[str, Backup] = {}
        for backup_path in self.backup_dir.glob("*.tar"):
            try:
                with tarfile.open(backup_path, "r:") as backup_file:
                    if data_file := backup_file.extractfile("./backup.json"):
                        data = json.loads(data_file.read())
                        backup = Backup(
                            slug=data["slug"],
                            name=data["name"],
                            date=data["date"],
                            path=backup_path,
                            size=round(backup_path.stat().st_size / 1_048_576, 2),
                        )
                        backups[backup.slug] = backup
            except (OSError, tarfile.TarError, json.JSONDecodeError, KeyError) as err:
                _LOGGER.warning("Unable to read backup %s: %s", backup_path, err)
        return backups


class YaDsk:
    """ Core integration class.
    Contains all method for YandexDisk communication.
    """
    _backup_observer = None
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
        """ File amount """
        return self._file_amount

    @property
    def file_markdown_list(self):
        """ File list in Markdown format """
        return self._file_markdown_list

    def __init__(self, hass: HomeAssistant, backup_observer: BackupObserver, config: dict, unique_id=None):
        self._options = {}
        self._options.update(config)
        self._token = config[CONF_TOKEN]
        self._refresh_token_value = config[CONF_REFRESH_TOKEN]
        self._token_expire_date: datetime.datetime = config.get(CONF_TOKEN_EXPIRES, datetime.datetime.now().isoformat())
        self._path = config[CONF_PATH]
        self._max_remote_file_amount = config[CONF_MAX_REMOTE_FILE]
        self._client_id = config[CONF_CLIENT_ID]
        self._client_s = config[CONF_CLIENT_SECRET]
        self._hass = hass
        self._backup_observer = backup_observer

    def get_info(self):
        """ Get class info """
        return "path: " + self._path

    def update_config(self, config: dict):
        """ Update class when integration config updated """
        self._options = {}
        self._options.update(config)
        self._path = config[CONF_PATH]
        self._max_remote_file_amount = config[CONF_MAX_REMOTE_FILE]
        self._token = config[CONF_TOKEN]
        self._refresh_token_value = config[CONF_REFRESH_TOKEN]
        self._token_expire_date = config.get(CONF_TOKEN_EXPIRES, datetime.datetime.now().isoformat())
        self._client_id = config[CONF_CLIENT_ID]
        self._client_s = config[CONF_CLIENT_SECRET]

        _LOGGER.info("Config updated to %s", self.get_info())

    def add_update_listener(self, coro):
        """Listeners to handle automatic data update."""
        self._update_listeners.append(coro)

    async def list_yandex_disk(self):
        """ List yandex disk directory. Async call from hass core/ """

        await self._hass.async_add_executor_job(self._list_yandex_disk)
        _LOGGER.debug("Count files result: %s", self.file_amount)

    def _list_yandex_disk(self):
        """ List yandex disk directory.

        Fill file amount< file Markdown list and file simple list.

        """
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
        """ Upload files to yandex. Assync call with hass core.

            Refresh token.
            Upload new files and delete old files from yandex disk.
            Refresh yandex disk directory information
        """
        await self._refresh_token_if_need(REFRESH_TOKEN_DELTA)

        local_backups = await self.get_local_files_list()
        await self.list_yandex_disk()

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
            await self.list_yandex_disk()

    async def get_local_files_list(self):
        """ Get list of home assistant backups """

        backups = await self._backup_observer.get_backups()

        result = {}
        for backup in backups.values():
            key = (backup.name + '_' + backup.slug).replace(" ","-").replace(":","_")
            if not self._upload_without_suffix:
                key += '.tar'
            result[key] = backup.path

        return result

    def _upload_file(self, y: yadisk.YaDisk, source_file, destination_file):
        """ Upload files to yandex disk """
        try:
            _LOGGER.info('Upload file %s to %s', source_file, destination_file)
            y.upload(source_file, destination_file, overwrite=True, n_retries=3, retry_interval=5,
                     timeout=(15.0, 250.0))
            _LOGGER.info('File %s uploaded to %s', source_file, destination_file)
        except Exception as e:
            _LOGGER.error("Error upload file %s", source_file, exc_info=True)
            raise e

    def _remove_file(self, y: yadisk.YaDisk, deleted_file):
        """ Remove files from yandex disk """
        try:
            _LOGGER.info('Remove file %s', deleted_file)
            y.remove(deleted_file, n_retries=3, retry_interval=5)
            _LOGGER.info('File %s removed', deleted_file)
        except Exception as e:
            _LOGGER.error("Error when remove file %s", deleted_file, exc_info=True)
            raise e

    async def _refresh_token_if_need(self, delta: datetime.timedelta):
        """ Refresh token when token lifetime go out bound """
        if (datetime.datetime.now() + delta) > datetime.datetime.fromisoformat(self._token_expire_date):
            _LOGGER.debug("Need refresh token")
            await self._refresh_token()
        else:
            _LOGGER.debug("Refresh token not needed")

    async def _refresh_token(self):
        """ Refresh token and save new token info in integration configuration """
        result = await self._hass.async_add_executor_job(_refresh_token_request, self._refresh_token_value,
                                                         self._client_id, self._client_s)

        self._refresh_token_value = result[CONF_REFRESH_TOKEN]
        self._token = result[CONF_TOKEN]
        self._token_expire_date = result[CONF_TOKEN_EXPIRES]
        self._options.update(result)

        await self._handle_update()

    async def _handle_update(self):
        """ Update integration configuration by changed class attributes """
        for coro in self._update_listeners:
            await coro(
                self._options
            )

    @staticmethod
    def _file_list_processing(objects: Generator[any, any, ResourceObject]) -> list:
        """ Processing file list, received from Yandex Disk """
        files = [obj for obj in objects if obj.type == TYPE_FILE]
        result = sorted(files, key=lambda obj: obj.modified, reverse=True)
        return result

    @staticmethod
    def _get_markdown_files(files: list[ResourceObject], max_items: int):
        """ Processing file list and form markdown formatting file list """
        if len(files) == 0:
            return ""

        result = "|name|modification|\n|---|---|"
        file_count = 0
        for file in files:
            result += "\n|{0:s}|{1:s}|".format(file.name, file.modified.strftime('%d.%m.%Y %H:%M:%S'))
            file_count += 1
            if file_count >= max_items:
                break
        return result
