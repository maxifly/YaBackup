from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
#
DOMAIN = 'yabackup'


async def async_setup(hass, hass_config):
    # used only with GUI setup
    hass.data[DOMAIN] = {}
    return True