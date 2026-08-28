from __future__ import annotations

from typing import Any

import click
import requests

from .base import BLOOMERP_IO_URL
from .credentials import load_api_key, load_organization_id


class BloomerpCliClient:
    def __init__(
        self,
        *,
        server_url: str = BLOOMERP_IO_URL,
        api_key: str | None = None,
        organization_id: str | None = None,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key if api_key is not None else load_api_key(self.server_url)
        self.organization_id = (
            organization_id
            if organization_id is not None
            else load_organization_id(self.server_url)
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        authentication_required: bool = True,
        allow_not_found: bool = False,
        **kwargs: Any,
    ) -> requests.Response:
        if authentication_required and not self.api_key:
            raise click.ClickException("Not logged in. Run 'bloomerp auth login'.")

        headers = dict(kwargs.pop("headers", {}))
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            timeout = kwargs.pop("timeout", 30)
            response = requests.request(
                method,
                f"{self.server_url}/{path.lstrip('/')}",
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise click.ClickException(
                f"Could not connect to Bloomerp.io at {self.server_url}: {exc}"
            ) from exc

        if response.status_code == 401:
            raise click.ClickException(
                "The Bloomerp.io API key is invalid or expired. Run 'bloomerp auth login'."
            )
        if allow_not_found and response.status_code == 404:
            return response
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                error_payload = response.json()
                detail = error_payload.get("detail")
                if not detail and isinstance(error_payload, dict):
                    detail = "; ".join(
                        f"{field}: {', '.join(map(str, messages))}"
                        if isinstance(messages, list)
                        else f"{field}: {messages}"
                        for field, messages in error_payload.items()
                    )
            except (ValueError, AttributeError, TypeError):
                detail = None
            raise click.ClickException(
                detail or f"Bloomerp.io returned HTTP {response.status_code}."
            ) from exc
        return response

    def session(self) -> dict:
        return self.request("GET", "/api/auth/session/").json()
