from __future__ import annotations

import click

from .search import search
from .show import show


@click.group()
def marketplace() -> None:
    """Discover apps in the Bloomerp marketplace."""


marketplace.add_command(search)
marketplace.add_command(show)

__all__ = ["marketplace"]
