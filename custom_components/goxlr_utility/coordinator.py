"""Coordinator for GoXLR Utility integration."""
from __future__ import annotations

import asyncio
from asyncio import Task
from datetime import timedelta
import logging
from typing import Any

from goxlrutilityapi.exceptions import (
    BadMessageException,
    ConnectionClosedException,
    ConnectionErrorException,
)
from goxlrutilityapi.helpers import get_mixer_from_status
from goxlrutilityapi.models.patch import Patch
from goxlrutilityapi.models.response import Response
from goxlrutilityapi.models.status import Mixer

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import GoXLRClient
from .const import DOMAIN
from .helper import CannotConnect, setup_connection
from .models import apply_patch


class GoXLRUtilityDataUpdateCoordinator(DataUpdateCoordinator[Mixer]):
    """Class to manage fetching GoXLR Utility data from single endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        LOGGER: logging.Logger,
        *,
        entry: ConfigEntry,
    ) -> None:
        """Initialize global GoXLR Utility data updater."""
        self._entry_data: dict[str, Any] = entry.data.copy()
        self._listener_task: Task | None = None
        self.client: GoXLRClient | None = None
        self.title = entry.title
        self.unsub: CALLBACK_TYPE | None = None

        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )

    @property
    def is_ready(self) -> bool:
        """Return if the data is ready."""
        return self.data is not None

    async def setup(self) -> None:
        """Set up connection to Websocket."""
        if self.unsub:
            self.unsub()
            self.unsub = None

        self.client = await setup_connection(
            self.hass,
            self._entry_data.copy(),
        )

        async def listen_for_patches() -> None:
            """Listen for patches from GoXLR Utility."""
            if self.client is None:
                raise ConfigEntryNotReady("Websocket not connected")

            try:
                await self.client.listen(self.patch_callback)
            except (
                ConnectionClosedException,
                ConnectionErrorException,
                ConnectionResetError,
            ) as exception:
                self.logger.debug(
                    "Websocket connection lost for %s. Will retry: %s",
                    self.title,
                    exception,
                )
            except BadMessageException as exception:
                self.logger.warning(
                    "Could not read a message from %s. Will reconnect: %s",
                    self.title,
                    exception,
                )

            await self.cleanup()
            self.last_update_success = False
            self.async_update_listeners()

        self._listener_task = self.hass.async_create_background_task(
            listen_for_patches(),
            name="GoXLR Utility Patch Listener",
        )

        async def cleanup(_: Event) -> None:
            """Disconnect and cleanup items."""
            self.unsub = None
            await self.cleanup()

        # Cleanup on Home Assistant shutdown
        self.unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP,
            cleanup,
        )

    async def cleanup(self) -> None:
        """Disconnect and cleanup items."""
        if self.client is not None:
            await self.client.disconnect()

    async def _get_mixer(self) -> Mixer:
        """Get mixer from GoXLR Utility."""
        if self.client is None or not self.client.connected:
            raise ConfigEntryNotReady("Websocket not connected")

        # Get status and mixer
        status = await self.client.get_status()
        mixer = get_mixer_from_status(status)
        if mixer is None:
            raise ConfigEntryNotReady("No mixer found")
        return mixer

    async def _patch_callback_task(
        self,
        patch: Patch,
    ) -> None:
        """Patch response callback task."""
        # Get new data
        new_data = self.data
        if new_data is None:
            self.logger.debug("No data available")
            return

        # Update data
        if not apply_patch(new_data, patch):
            self.logger.debug("Unused patch received: %s", patch.path)
            return
        self.logger.info("Update '%s': %s", patch.path, patch.value)
        self.logger.debug("Updated data: %s", new_data)
        self.async_set_updated_data(new_data)

        # Update listeners
        self.last_update_success = True
        self.async_update_listeners()

    async def patch_callback(
        self,
        response: Response[Patch],
    ) -> None:
        """Patch response callback function."""
        self.hass.async_create_background_task(
            self._patch_callback_task(response.data),
            name="Patch Callback Task",
        )

    async def _async_update_data(self) -> Mixer:
        """Check the connection, reconnecting and reading the status if it was lost."""
        connection_lost = (
            self.client is None
            or not self.client.connected
            or self._listener_task is None
            or self._listener_task.done()
        )
        if connection_lost:
            await self.cleanup()
            try:
                await self.setup()
            except (asyncio.TimeoutError, CannotConnect) as exception:
                raise UpdateFailed(
                    f"Could not connect to GoXLR Utility: {exception}"
                ) from exception

        if connection_lost or self.data is None:
            try:
                return await self._get_mixer()
            except (
                BadMessageException,
                ConfigEntryNotReady,
                ConnectionClosedException,
            ) as exception:
                await self.cleanup()
                raise UpdateFailed(
                    f"Could not read the GoXLR Utility status: {exception}"
                ) from exception

        return self.data
