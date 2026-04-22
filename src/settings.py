from __future__ import annotations

import importlib
import os
from types import ModuleType

try:
    _LEGACY_CONFIG: ModuleType | None = importlib.import_module("ow_config")
except ModuleNotFoundError:  # pragma: no cover - legacy config is optional
    _LEGACY_CONFIG = None


def _read(name: str, default: object = None, legacy_name: str | None = None) -> object:
    if name in os.environ:
        return os.environ[name]

    if legacy_name and _LEGACY_CONFIG is not None and hasattr(_LEGACY_CONFIG, legacy_name):
        return getattr(_LEGACY_CONFIG, legacy_name)

    if _LEGACY_CONFIG is not None and hasattr(_LEGACY_CONFIG, name):
        return getattr(_LEGACY_CONFIG, name)

    return default


def _read_str(name: str, default: str = "", legacy_name: str | None = None) -> str:
    value = _read(name=name, default=default, legacy_name=legacy_name)
    if value is None:
        return default
    return str(value)


def _read_int(name: str, default: int, legacy_name: str | None = None) -> int:
    value = _read(name=name, default=default, legacy_name=legacy_name)
    try:
        if isinstance(value, (int, float, str, bytes, bytearray)):
            return int(value)
    except (TypeError, ValueError):
        pass
    return default


MANAGER_URL = _read_str(
    "MANAGER_URL", "http://127.0.0.1:7776/api/accounts", "manager_url"
)
ACCESS_SERVICE_TOKEN = _read_str(
    "ACCESS_SERVICE_TOKEN", "", "access_service_token"
)
ACCESS_CALLBACK_TOKEN = _read_str(
    "ACCESS_CALLBACK_TOKEN", "", "access_callback_token"
)
REQUEST_TIMEOUT_SECONDS = _read_int(
    "REQUEST_TIMEOUT_SECONDS", 30, "request_timeout_seconds"
)
LOG_LEVEL = _read_str("LOG_LEVEL", "INFO")
