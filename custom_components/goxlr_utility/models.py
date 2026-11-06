"""Model fixes for GoXLR Utility integration."""
from __future__ import annotations

from typing import Any

from goxlrutilityapi.const import MODEL_MAP, RESPONSE_TYPE_PATCH, RESPONSE_TYPE_STATUS
from goxlrutilityapi.models import patch, status
from pydantic import BaseModel


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


class Patch(patch.Patch):
    """Patch model, a patch that removes something has no value."""

    value: Any = None


def register_models() -> None:
    """Parse GoXLR Utility messages with the fixed models."""
    MODEL_MAP[RESPONSE_TYPE_PATCH] = Patch
    MODEL_MAP[RESPONSE_TYPE_STATUS] = Status


def apply_patch(mixer: status.Mixer, update: patch.Patch) -> bool:
    """Apply a patch to a mixer, which holds models, plain dicts and lists.

    Returns False when the patch is not for a mixer or its path does not exist.
    """
    keys = update.path.split("/")
    if len(keys) <= 3 or keys[1] != "mixers":
        return False

    try:
        target: Any = mixer
        for key in keys[3:-1]:
            target = _get_item(target, key)
        _set_item(target, keys[-1], update)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False
    return True


def _field_name(model: BaseModel, key: str) -> str:
    """Return the name of the model field that has this key as its alias."""
    for name, field in type(model).model_fields.items():
        if field.alias == key:
            return name
    return key


def _get_item(target: Any, key: str) -> Any:
    """Return an item of a model, list or dict."""
    if isinstance(target, BaseModel):
        return getattr(target, _field_name(target, key))
    if isinstance(target, list):
        return target[int(key)]
    return target[key]


def _set_item(target: Any, key: str, update: patch.Patch) -> None:
    """Add, replace or remove an item of a model, list or dict."""
    if isinstance(target, BaseModel):
        value = None if update.op == "remove" else update.value
        setattr(target, _field_name(target, key), value)
    elif isinstance(target, list):
        if update.op == "add":
            target.insert(len(target) if key == "-" else int(key), update.value)
        elif update.op == "remove":
            del target[int(key)]
        else:
            target[int(key)] = update.value
    elif update.op == "remove":
        del target[key]
    else:
        target[key] = update.value
