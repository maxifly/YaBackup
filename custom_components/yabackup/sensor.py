"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry

# from __future__ import annotations


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    add_entities([ExampleSensor(config, None)], True)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities):
    entity = ExampleSensor(entry.options, entry.entry_id)
    async_add_entities([entity], True)

    hass.data[DOMAIN][entry.entry_id] = entity


class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = "Example Temperature"
    # _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, config: dict, unique_id=None):
        i = 1

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = 23
