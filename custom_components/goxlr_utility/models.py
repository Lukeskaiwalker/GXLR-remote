"""Model fixes for GoXLR Utility integration."""
from __future__ import annotations

from goxlrutilityapi.const import MODEL_MAP, RESPONSE_TYPE_STATUS
from goxlrutilityapi.models import status


class UsbDevice(status.UsbDevice):
    """USB device model, GoXLR Utility on macOS sends no identifier."""

    identifier: str | None = None


class Hardware(status.Hardware):
    """Hardware model using the fixed USB device model."""

    usb_device: UsbDevice


class Mixer(status.Mixer):
    """Mixer model using the fixed hardware model."""

    hardware: Hardware


class Status(status.Status):
    """Status model using the fixed mixer model."""

    mixers: dict[str, Mixer]


def register_models() -> None:
    """Parse GoXLR Utility status responses with the fixed models."""
    MODEL_MAP[RESPONSE_TYPE_STATUS] = Status
