from __future__ import annotations

import json
import os
from pathlib import Path

from platformdirs import user_config_path

from .base import BLOOMERP_IO_URL


def credentials_path() -> Path:
    override = os.environ.get("BLOOMERP_CREDENTIALS_FILE")
    if override:
        return Path(override).expanduser()
    return user_config_path("bloomerp") / "credentials.json"


def _read_credentials() -> dict:
    path = credentials_path()
    if not path.exists():
        return {"profiles": {}}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"profiles": {}}

    if not isinstance(payload, dict) or not isinstance(payload.get("profiles"), dict):
        return {"profiles": {}}
    return payload


def _write_credentials(payload: dict) -> None:
    path = credentials_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.chmod(0o600)
    temporary_path.replace(path)
    path.chmod(0o600)


def load_api_key(server_url: str = BLOOMERP_IO_URL) -> str | None:
    environment_key = os.environ.get("BLOOMERP_API_KEY", "").strip()
    if environment_key:
        return environment_key

    profile = _read_credentials()["profiles"].get(server_url.rstrip("/"), {})
    api_key = profile.get("api_key") if isinstance(profile, dict) else None
    return str(api_key).strip() if api_key else None


def save_api_key(api_key: str, server_url: str = BLOOMERP_IO_URL) -> None:
    payload = _read_credentials()
    profile = payload["profiles"].setdefault(server_url.rstrip("/"), {})
    profile["api_key"] = api_key
    _write_credentials(payload)


def load_organization_id(server_url: str = BLOOMERP_IO_URL) -> str | None:
    profile = _read_credentials()["profiles"].get(server_url.rstrip("/"), {})
    organization_id = (
        profile.get("organization_id") if isinstance(profile, dict) else None
    )
    return str(organization_id).strip() if organization_id else None


def save_organization_id(
    organization_id: str,
    server_url: str = BLOOMERP_IO_URL,
) -> None:
    payload = _read_credentials()
    profile = payload["profiles"].setdefault(server_url.rstrip("/"), {})
    profile["organization_id"] = organization_id
    _write_credentials(payload)


def delete_api_key(server_url: str = BLOOMERP_IO_URL) -> bool:
    payload = _read_credentials()
    removed = payload["profiles"].pop(server_url.rstrip("/"), None) is not None
    if removed:
        _write_credentials(payload)
    return removed
