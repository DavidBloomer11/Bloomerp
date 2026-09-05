from __future__ import annotations

import click

from .search import search
from .manage import add, remove, resolve, develop


@click.group()
def marketplace() -> None:
    """Discover apps in the Bloomerp marketplace."""


marketplace.add_command(search)


__all__ = ["marketplace"]

for command in (add, remove, resolve, develop):
    marketplace.add_command(command)
