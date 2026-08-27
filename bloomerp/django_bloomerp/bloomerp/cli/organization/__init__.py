from __future__ import annotations

import click

from .list import list_organizations
from .use import use


@click.group()
def organization() -> None:
    """List and select Bloomerp.io organizations."""


organization.add_command(list_organizations)
organization.add_command(use)

__all__ = ["organization"]
