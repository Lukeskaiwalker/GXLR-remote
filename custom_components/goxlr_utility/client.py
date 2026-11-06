"""GoXLR Utility client with what the library does not provide."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from typing import Any

from goxlrutilityapi.const import REQUEST_TYPE_COMMAND, RESPONSE_TYPE_OK
from goxlrutilityapi.exceptions import BadMessageException
from goxlrutilityapi.models.request import Request
from goxlrutilityapi.websocket_client import WebsocketClient

_LOGGER = logging.getLogger(__name__)


class GoXLRClient(WebsocketClient):
    """Websocket client that also sets fader labels and handles command replies."""

    async def _listen_for_messages(
        self,
        callback: Callable[[dict[Any, Any]], Awaitable[None]],
    ) -> None:
        """Listen for messages, handling the replies the library can't parse."""

        async def _handle_message(message: dict[Any, Any]) -> None:
            data = message.get("data")
            if isinstance(data, str):
                return
            if isinstance(data, dict) and "Error" in data:
                _LOGGER.warning("GoXLR Utility rejected a command: %s", data["Error"])
                return
            await callback(message)

        await super()._listen_for_messages(_handle_message)

    async def set_fader_label(
        self,
        fader: str,
        text: str | None = None,
        icon: str | None = None,
    ) -> None:
        """Set the text and icon on a fader's display.

        None keeps the current text or icon, an empty icon removes it.
        """
        if self._mixer_serial_number is None:
            raise BadMessageException(
                "Mixer serial number is missing. Call get_status to set this."
            )

        commands: list[dict[str, list[str | None]]] = []
        if icon is not None:
            commands.append({"SetScribbleIcon": [fader, icon or None]})
        if text is not None:
            commands.append({"SetScribbleText": [fader, text]})

        for command in commands:
            await self._send_message(
                Request(
                    data={REQUEST_TYPE_COMMAND: [self._mixer_serial_number, command]}
                ),
                wait_for_response=False,
                response_type=RESPONSE_TYPE_OK,
            )
