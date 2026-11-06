"""The GoXLR Utility integration."""
from __future__ import annotations

import asyncio
import logging

from goxlrutilityapi.exceptions import BadMessageException, ConnectionClosedException
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import GoXLRUtilityDataUpdateCoordinator
from .helper import CannotConnect

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
]

SERVICE_SET_FADER_LABEL = "set_fader_label"
SERVICE_SET_FADER_LABEL_SCHEMA = vol.Schema(
    {
        vol.Required("fader"): vol.In(["A", "B", "C", "D"]),
        vol.Optional("text"): cv.string,
        vol.Optional("icon"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the GoXLR Utility actions."""

    async def async_set_fader_label(call: ServiceCall) -> None:
        """Set the text and icon on a fader's display."""
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if not coordinators:
            raise HomeAssistantError("GoXLR Utility is not connected")

        for coordinator in coordinators:
            try:
                await coordinator.client.set_fader_label(
                    call.data["fader"],
                    call.data.get("text"),
                    call.data.get("icon"),
                )
            except (BadMessageException, ConnectionClosedException) as exception:
                raise HomeAssistantError(
                    f"Could not set the fader label: {exception}"
                ) from exception

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FADER_LABEL,
        async_set_fader_label,
        schema=SERVICE_SET_FADER_LABEL_SCHEMA,
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up GoXLR Utility from a config entry."""
    coordinator = GoXLRUtilityDataUpdateCoordinator(
        hass,
        _LOGGER,
        entry=entry,
    )

    try:
        await coordinator.setup()
    except (asyncio.TimeoutError, CannotConnect) as exception:
        raise ConfigEntryNotReady(exception) from exception

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload entry when its updated.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: GoXLRUtilityDataUpdateCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]
        await coordinator.cleanup()

        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)
