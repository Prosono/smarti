import logging
import aiohttp 
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .updater import check_for_update, update_files, update_manifest_version

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smarti"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SMARTi from a config entry."""
    async_add_entities([SmartiUpdaterEntity(hass, entry)])

class SmartiUpdaterEntity(UpdateEntity):
    """Representation of an update entity for SMARTi."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the entity."""
        self.hass = hass
        self.entry = entry
        self._attr_installed_version = entry.version
        self._attr_latest_version = None
        self._attr_release_url = "https://github.com/Prosono/smarti/releases"
        self._attr_entity_picture = "https://brands.home-assistant.io/_/smartiupdater/icon.png"
        self._attr_in_progress = False
        self._attr_supported_features = UpdateEntityFeature.INSTALL
        self._attr_unique_id = f"{entry.entry_id}_updater"

    @property
    def name(self):
        """Return the name of the update entity."""
        return "SMARTi"

    @property
    def entity_category(self):
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_update(self):
        """Fetch the latest version from GitHub."""
        async with aiohttp.ClientSession() as session:
            update_available, latest_version = await check_for_update(session, self._attr_installed_version)
            _LOGGER.debug(f"Fetched latest version: {latest_version}")
            self._attr_latest_version = latest_version
            self._available = update_available
            self.async_write_ha_state()  # Update the entity state without triggering an install

    async def async_install(self, version=None, backup=False):
        """Install the update when triggered by the user."""
        self._attr_in_progress = True
        self.async_write_ha_state()
        async with aiohttp.ClientSession() as session:
            await update_files(session)  # Perform the update
            await update_manifest_version(self._attr_latest_version)
        self._attr_installed_version = self._attr_latest_version
        self._attr_in_progress = False
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "smarti")},
            name="SMARTi",
            manufacturer="Your Name or Company",
        )
