import aiohttp
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import persistent_notification
from .updater import update_files, check_for_update, update_manifest_version
#Added comment her for testing
_LOGGER = logging.getLogger(__name__)

DOMAIN = "smarti"

async def async_setup(hass: HomeAssistant, config: dict):
    _LOGGER.info("Setting up the SMARTi integration.")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("Setting up SMARTi from config entry.")

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "update")
    )

    async def update_service(call):
        _LOGGER.info("The SMARTi service was called.")
        async with aiohttp.ClientSession() as session:
            current_version = entry.version
            update_available, latest_version = await check_for_update(session, current_version)

            if update_available:
                await update_files(session)
                await update_manifest_version(latest_version)
                hass.config_entries.async_update_entry(entry, version=latest_version)
                persistent_notification.async_create(
                    hass,
                    f"SMARTi Service Completed! Updated to version {latest_version}.",
                    title="SMARTi",
                    notification_id="SMARTi"
                )
            else:
                _LOGGER.info("Smarti Updater: No updates available.")
                persistent_notification.async_create(
                    hass,
                    "SMARTi Service Completed! No updates were available.",
                    title="SMARTi",
                    notification_id="SMARTi"
                )

    hass.services.async_register(DOMAIN, "update", update_service)
    _LOGGER.info("SMARTi service registered successfully.")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info("Unloading SMARTi config entry.")

    await hass.config_entries.async_forward_entry_unload(entry, "update")

    if hass.services.has_service(DOMAIN, "update"):
        hass.services.async_remove(DOMAIN, "update")

    hass.data[DOMAIN].pop(entry.entry_id)
    return True

async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.info(f"Migrating from version {entry.version}")

    async with aiohttp.ClientSession() as session:
        update_available, latest_version = await check_for_update(session, entry.version)

    if entry.version != latest_version:
        hass.config_entries.async_update_entry(entry, version=latest_version)
        _LOGGER.info(f"Migration to version {latest_version} successful")
    else:
        _LOGGER.info("No migration necessary")

    return True