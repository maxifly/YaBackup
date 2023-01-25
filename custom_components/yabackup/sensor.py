""" Integration sensors """
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .constants import DOMAIN
from .yad import YaDsk

_LOGGER = logging.getLogger(__name__)
MARKDOWN_FILES = "markdown_file_list"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities):
    """ Create all integration sensors """
    ya_disk = hass.data[DOMAIN][entry.entry_id]

    entity = DiskInfoSensor(ya_disk)
    async_add_entities([entity], True)

    # hass.data[DOMAIN][entry.entry_id] = entity


class DiskInfoSensor(SensorEntity):
    """ Sensor with information about YandexDisk directory """

    _attr_name = DOMAIN + "_disk_info"
    # _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.MEASUREMENT

    _attr_extra_state_attributes = {MARKDOWN_FILES: ""}
    _ya_dsk = None

    def __init__(self, ya_dsk: YaDsk):
        self._ya_dsk = ya_dsk

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = self._ya_dsk.file_amount
        self._attr_extra_state_attributes[MARKDOWN_FILES] = self._ya_dsk.file_markdown_list

        _LOGGER.debug("markdown " + self._ya_dsk.file_markdown_list)
