import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .constants import DOMAIN
from .yad import YaDsk

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities):
    ya_disk = hass.data[DOMAIN][entry.entry_id]

    entity1 = UpdateButton(ya_disk)
    entity2 = UploadButton(ya_disk)
    async_add_entities([entity1, entity2], True)


class UpdateButton(ButtonEntity):
    """Representation of a Button."""

    _attr_name = DOMAIN + "_update_button"

    _ya_dsk: YaDsk = None

    def __init__(self, ya_dsk: YaDsk):
        _LOGGER.debug("Create update button")
        self._ya_dsk = ya_dsk

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._ya_dsk.count_files()
        _LOGGER.debug("Button press processed")


class UploadButton(ButtonEntity):
    """Representation of a Button."""

    _attr_name = DOMAIN + "_upload_button"

    _ya_dsk: YaDsk = None

    def __init__(self, ya_dsk: YaDsk):
        _LOGGER.debug("Create update button")
        self._ya_dsk = ya_dsk

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._ya_dsk.upload_files()
        _LOGGER.debug("Upload button press processed")
