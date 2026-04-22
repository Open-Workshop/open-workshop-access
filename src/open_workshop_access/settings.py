from __future__ import annotations

import os


def _read(name: str, default: object = None) -> object:
    return os.environ.get(name, default)


def _read_str(name: str, default: str = "") -> str:
    value = _read(name=name, default=default)
    if value is None:
        return default
    return str(value)


def _read_int(name: str, default: int) -> int:
    value = _read(name=name, default=default)
    try:
        if isinstance(value, (int, float, str, bytes, bytearray)):
            return int(value)
    except (TypeError, ValueError):
        pass
    return default


MANAGER_URL = _read_str("MANAGER_URL", "http://127.0.0.1:7776/api/accounts")
ACCESS_CALLBACK_TOKEN = _read_str("ACCESS_CALLBACK_TOKEN", "")
REQUEST_TIMEOUT_SECONDS = _read_int("REQUEST_TIMEOUT_SECONDS", 30)
LOG_LEVEL = _read_str("LOG_LEVEL", "INFO")
