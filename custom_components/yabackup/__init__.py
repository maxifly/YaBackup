from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .constants import DOMAIN
from .yad import YaDsk

#
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass, hass_config):
    # used only with GUI setup
    hass.data[DOMAIN] = {}
    _LOGGER.info("async_setup")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("async_setup_entry")

    # migrate data (after first setup) to options
    if entry.data:
        hass.config_entries.async_update_entry(entry, data={},
                                               options=entry.data)

    # add options handler
    entry.add_update_listener(async_update_options)

    ya_dsk = YaDsk(entry.options, entry.entry_id)

    _LOGGER.info("Create YaDisk " + ya_dsk.get_info())

    hass.data[DOMAIN][entry.entry_id] = ya_dsk
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    # update entity config
    hass.data[DOMAIN][entry.entry_id].update_config(entry.options)

